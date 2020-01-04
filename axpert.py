#! /usr/bin/python

# Axpert Inverter control script

# switch mode to electric low or high tarif 
# calculation of CRC is done by XMODEM mode, but in firmware is wierd mistake in POP02 command, so exception of calculation is done in serial_command(command) function
# real PL2303 = big trouble in my setup, cheap chinese converter some times disconnecting, workaround is at the end of serial_command(command) function
# differenc between SBU(POP02) and Solar First (POP01): in state POP01 inverter works only if PV_voltage <> 0 !!! SBU mode works during night


import serial, time, sys, string
import os
import re
import crcmod
import usb.core
import usb.util
import sys
import signal
import time
from binascii import unhexlify
#import binascii

connection = "serial"
#connection = "USB"

#Axpert Commands and examples
#Q1		# Undocumented command: LocalInverterStatus (seconds from absorb), ParaExistInfo (seconds from end of Float), SccOkFlag, AllowSccOnFlag, ChargeAverageCurrent, SCC PWM Temperature, Inverter Temperature, Battery Temperature, Transformer Temperature, GPDAT, FanLockStatus, FanPWMDuty, FanPWM, SCCChargePowerWatts, ParaWarning, SYNFreq, InverterChargeStatus
#QPI            # Device protocol ID inquiry
#QID            # The device serial number inquiry
#QVFW           # Main CPU Firmware version inquiry
#QVFW2          # Another CPU Firmware version inquiry
#QFLAG          # Device flag status inquiry
#QPIGS          # Device general status parameters inquiry
                # GridVoltage, GridFrequency, OutputVoltage, OutputFrequency, OutputApparentPower, OutputActivePower, OutputLoadPercent, BusVoltage, BatteryVoltage, BatteryChargingCurrent, BatteryCapacity, InverterHeatSinkTemperature, PV-InputCurrentForBattery, PV-InputVoltage, BatteryVoltageFromSCC, BatteryDischargeCurrent, DeviceStatus,
#QMOD           # Device mode inquiry P: PowerOnMode, S: StandbyMode, L: LineMode, B: BatteryMode, F: FaultMode, H: PowerSavingMode
#QPIWS          # Device warning status inquiry: Reserved, InverterFault, BusOver, BusUnder, BusSoftFail, LineFail, OPVShort, InverterVoltageTooLow, InverterVoltageTooHIGH, OverTemperature, FanLocked, BatteryVoltageHigh, BatteryLowAlarm, Reserved, ButteryUnderShutdown, Reserved, OverLoad, EEPROMFault, InverterSoftFail, SelfTestFail, OPDCVoltageOver, BatOpen, CurrentSensorFail, BatteryShort, PowerLimit, PVVoltageHigh, MPPTOverloadFault, MPPTOverloadWarning, BatteryTooLowToCharge, Reserved, Reserved
#QDI            # The default setting value information
#QMCHGCR        # Enquiry selectable value about max charging current
#QMUCHGCR       # Enquiry selectable value about max utility charging current
#QBOOT          # Enquiry DSP has bootstrap or not
#QOPM           # Enquiry output mode
#QPIRI          # Device rating information inquiry - nefunguje
#QPGS0          # Parallel information inquiry
                # TheParallelNumber, SerialNumber, WorkMode, FaultCode, GridVoltage, GridFrequency, OutputVoltage, OutputFrequency, OutputAparentPower, OutputActivePower, LoadPercentage, BatteryVoltage, BatteryChargingCurrent, BatteryCapacity, PV-InputVoltage, TotalChargingCurrent, Total-AC-OutputApparentPower, Total-AC-OutputActivePower, Total-AC-OutputPercentage, InverterStatus, OutputMode, ChargerSourcePriority, MaxChargeCurrent, MaxChargerRange, Max-AC-ChargerCurrent, PV-InputCurrentForBattery, BatteryDischargeCurrent
#QBV		# Compensated Voltage, SoC
#PEXXX          # Setting some status enable
#PDXXX          # Setting some status disable
#PF             # Setting control parameter to default value
#FXX            # Setting device output rating frequency
#POP02          # set to SBU
#POP01          # set to Solar First
#POP00          # Set to UTILITY
#PBCVXX_X       # Set battery re-charge voltage
#PBDVXX_X       # Set battery re-discharge voltage
#PCP00          # Setting device charger priority: Utility First
#PCP01          # Setting device charger priority: Solar First
#PCP02          # Setting device charger priority: Solar and Utility
#PGRXX          # Setting device grid working range
#PBTXX          # Setting battery type
#PSDVXX_X       # Setting battery cut-off voltage
#PCVVXX_X       # Setting battery C.V. charging voltage
#PBFTXX_X       # Setting battery float charging voltage
#PPVOCKCX       # Setting PV OK condition
#PSPBX          # Setting solar power balance
#MCHGC0XX       # Setting max charging Current          M XX
#MUCHGC002      # Setting utility max charging current  0 02
#MUCHGC010      # Setting utility max charging current  0 10
#MUCHGC020      # Setting utility max charging current  0 20
#MUCHGC030      # Setting utility max charging current  0 30
#POPMMX         # Set output mode       M 0:single, 1: parrallel, 2: PH1, 3: PH2, 4: PH3

#notworking
#PPCP000        # Setting parallel device charger priority: UtilityFirst - notworking
#PPCP001        # Setting parallel device charger priority: SolarFirst - notworking
#PPCP002        # Setting parallel device charger priority: OnlySolarCharging - notworking

def handler(signum, frame):
    print 'Signal handler called with signal', signum
    raise Exception("Handler")

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 2400
ser.bytesize = serial.EIGHTBITS     #number of bits per bytes
ser.parity = serial.PARITY_NONE     #set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE  #number of stop bits
ser.timeout = 1                     #non-block read
ser.xonxoff = False                 #disable software flow control
ser.rtscts = False                  #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False                  #disable hardware (DSR/DTR) flow control
ser.writeTimeout = 2                #timeout for write

try:
    usb0 = os.open('/dev/hidraw0', os.O_RDWR | os.O_NONBLOCK)
    usb1 = os.open('/dev/hidraw1', os.O_RDWR | os.O_NONBLOCK)

except Exception, e:
    print "error open USB port: " + str(e)
    exit()
    
def get_output_source_priority():
    #get inverter output mode priority
    output_source_priority = "8"
    try:
	if ( connection == "serial" and ser.isOpen() or connection == "USB" ):
            response = serial_command("QPIRI",usb0)
            if "NAKss" in response:
                if connection == "serial": time.sleep(0.5)
                return ""
            response.rstrip()
            nums = response.split(' ', 99)
            output_source_priority = nums[16]

    	elif ( connection == "serial" ):
            ser.close()
            print "cannot use serial port ..."
            return ""

    except Exception, e:
            print "error parsing inverter data...: " + str(e)
            return ""

    return output_source_priority

def get_charger_source_priority():
    #get inverter charger mode priority
    charger_source_priority = "8"
    try:
	if ( connection == "serial" and ser.isOpen() or connection == "USB" ):
            response = serial_command("QPIRI",usb0)
            if "NAKss" in response:
                if connection == "serial": time.sleep(0.5)
                return ""
            response.rstrip()
            nums = response.split(' ', 99)
            charger_source_priority = nums[17]

    	elif ( connection == "serial" ):
            ser.close()
            print "cannot use serial port ..."
            return ""

    except Exception, e:
            print "error parsing inverter data...: " + str(e)
            return ""

    return charger_source_priority

def set_output_source_priority(output_source_priority):
    #set inverter output mode priority
        if not output_source_priority == "":
    	    try:
		if ( connection == "serial" and ser.isOpen() or connection == "USB" ):
                    if output_source_priority == 0:
                        response = serial_command("POP00",usb0)
                        print response
                    elif output_source_priority == 1:
                        response = serial_command("POP01",usb0)
                        print response
                    elif output_source_priority == 2:
                        response = serial_command("POP02",usb0)
                        print response

    		elif ( connection == "serial" ):
        	    ser.close()
        	    print "cannot use serial port ..."
        	    return ""

    	    except Exception, e:
                print "error parsing inverter data...: " + str(e)
                return ''

        return 1

def set_charger_source_priority(charger_source_priority):
    #set inverter charge mode priority
        if not charger_source_priority == "":
            try:
		if ( connection == "serial" and ser.isOpen() or connection == "USB" ):

                    if charger_source_priority == 0:
                        response = serial_command("PCP00",usb0)
                        print response
                    elif charger_source_priority == 1:
                        response = serial_command("PCP01",usb0)
                        print response
                    elif charger_source_priority == 2:
                        response = serial_command("PCP02",usb0)
                        print response
                    elif charger_source_priority == 3:
                        response = serial_command("PCP03",usb0)
                        print response

    		elif ( connection == "serial" ):
        	    ser.close()
        	    print "cannot use serial port ..."
        	    return ""

            except Exception, e:
                    print "error parsing inverter data...: " + str(e)
                    return ''

        return 1


def serial_command(command,device):
    try:
	response = ""
	xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
	# wierd mistake in Axpert firmware - correct CRC is: 0xE2 0x0A
        if command == "POP02": command_crc = '\x50\x4f\x50\x30\x32\xe2\x0b\x0d\r'
        else: command_crc = command + unhexlify(hex(xmodem_crc_func(command)).replace('0x','',1)) + '\r'
	
	# Set the signal handler and a 5-second alarm 
	signal.signal(signal.SIGALRM, handler)
	signal.alarm(10)
	if len (command_crc) < 9:
	    time.sleep (0.35)
	    os.write(device, command_crc)
	    
	else:
	    cmd1 = command_crc[:8]
	    cmd2 = command_crc[8:]
	    time.sleep (0.35)
	    os.write(device, cmd1)
	    time.sleep (0.35)
	    os.write(device, cmd2)
	    time.sleep (0.25)
	while True:
	    time.sleep (0.15)
	    r = os.read(device, 256)
	    response += r
	    if '\r' in r: break

    except Exception, e:
        print "error reading inverter...: " + str(e) + "Response :" + response
        data = ""
        if connection == "serial":
	    time.sleep(20)  # Problem with some USB-Serial adapters, they are some times disconnecting, 20 second helps to reconnect at same ttySxx
	    ser.open()
	    time.sleep(0.5)
            return ''

    signal.alarm(0)

    sys.stdout.write (command + " : ")
    sys.stdout.flush ()
    print response
    return response


def main(switchMode):
    while True:
        output_source_priority = get_output_source_priority()
        charger_source_priority = get_charger_source_priority()
        if not output_source_priority == "8":
            if not charger_source_priority == "8": 
                break
        time.sleep(30) 
                
    if switchMode == "VALLE":           
        print "Change to VALLE"  # electricity is cheap, so charge batteries from grid and hold them fully charged! important for Lead Acid Batteries Only!
        if not output_source_priority == "0":       # Utility First (0: Utility first, 1: Solar First, 2: SBU)
            set_output_source_priority(0)
        if not charger_source_priority == "0":      # Utility First (0: Utility first, 1: Solar First, 2: Solar+Utility, 3: Solar Only)
            set_charger_source_priority(2)

    elif switchMode == "PICO":   
        print "Change to PICO"  # electricity is expensive, so supply everything from batteries not from grid
        if not output_source_priority == "2":       # Utility First (0: Utility first, 1: Solar First, 2: SBU)
            set_output_source_priority(2)
        if not charger_source_priority == "3":      # Utility First (0: Utility first, 1: Solar First, 2: Solar+Utility, 3: Solar Only)
            set_charger_source_priority(3)

    ser.close()

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--switch', default='',
                        help='Switch to PICO o VALLE mode inverter')
    args = parser.parse_args()
    switchMode = args.switch
    if not switchMode == '':
        main(switchMode)
