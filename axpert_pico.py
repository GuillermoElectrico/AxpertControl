#!/usr/bin/env python3

import serial, time, sys, string     # pip3 install pyserial
import os
import re
import crcmod
import telegram                      #  pip3 install python-telegram-bot
from binascii import unhexlify
from datetime import datetime

#Commands with CRC cheats
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
#QPGS0          # Parallel information inquiry
                # TheParallelNumber, SerialNumber, WorkMode, FaultCode, GridVoltage, GridFrequency, OutputVoltage, OutputFrequency, OutputAparentPower, OutputActivePower, LoadPercentage, BatteryVoltage, BatteryChargingCurrent, BatteryCapacity, PV-InputVoltage, TotalChargingCurrent, Total-AC-OutputApparentPower, Total-AC-OutputActivePower, Total-AC-OutputPercentage, InverterStatus, OutputMode, ChargerSourcePriority, MaxChargeCurrent, MaxChargerRange, Max-AC-ChargerCurrent, PV-InputCurrentForBattery, BatteryDischargeCurrent
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

#nefunkcni
#QPIRI          # Device rating information inquiry - nefunguje
#PPCP000        # Setting parallel device charger priority: UtilityFirst - nefunguje
#PPCP001        # Setting parallel device charger priority: SolarFirst - nefunguje
#PPCP002        # Setting parallel device charger priority: OnlySolarCharging - nefunguje

ser = serial.Serial()
ser.port = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
ser.baudrate = 2400
ser.bytesize = serial.EIGHTBITS     #number of bits per bytes
ser.parity = serial.PARITY_NONE     #set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE  #number of stop bits
ser.timeout = 3                     #non-block read
ser.xonxoff = False                 #disable software flow control
ser.rtscts = False                  #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False                  #disable hardware (DSR/DTR) flow control
ser.write_Timeout = 5                #timeout for write

#token that can be generated talking with @BotFather on telegram
token = ""
if token != "":
    bot = telegram.Bot(token=token)
"""
Send a mensage to a telegram user specified on chatId
chat_id must be a number! 
use @userinfobot to obtain yout userID from a private conversation
"""
chat_id=""

try:
    ser.open()

except Exception as e:
    text = "error open serial port: " + str(e)
    print (text)
    if token != "":
        bot.sendMessage(chat_id=chat_id, text=text)
    exit()

try:
    # datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print ("RUN =", dt_string)

    # obtain actual information inverter
    ser.flushInput()            #flush input buffer, discarding all its contents
    ser.flushOutput()           #flush output buffer, aborting current output and discard all that is in buffer
    command = "QPIRI"
    print (command)
    xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
    command_crc = command + (unhexlify(hex(xmodem_crc_func(command.encode('utf-8'))).replace('0x','',1))).decode('utf-8', 'ignore') + '\x0d'
    ser.write(command_crc.encode())
    response = ser.readline()
    print (response)

    if b"NAKss" in response:
        text = "error serial port (NAKss)"
        print (text)
        if token != "":
            bot.sendMessage(chat_id=chat_id, text=text)
        #delay time
        print ("Delay 10 second")
        time.sleep(10)
        # obtain Device protocol ID inquiry (to reboot connection after restart inverter)
        ser.flushInput()            #flush input buffer, discarding all its contents
        ser.flushOutput()           #flush output buffer, aborting current output and discard all that is in buffer
        command = "QPI"
        print (command)
        xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
        command_crc = command + (unhexlify(hex(xmodem_crc_func(command.encode('utf-8'))).replace('0x','',1))).decode('utf-8', 'ignore') + '\x0d'
        ser.write(command_crc.encode())
        response2 = ser.readline()
        print (response2)
        if b"NAKss" in response2:
            text = "error initializing serial port (NAKss)"
            print (text)
            if token != "":
                bot.sendMessage(chat_id=chat_id, text=text)
        exit()

    response.rstrip()
    nums = response.split(b' ', 99)
    output_source_priority = nums[16]
    charger_source_priority = nums[17]
    print ("Output mode (0: Utility first, 1: Solar First, 2: SBU)")
    print (output_source_priority.decode())
    print ("Charge mode (0: Utility first, 1: Solar First, 2: Solar+Utility, 3: Solar Only)")
    print (charger_source_priority.decode())

    # if information if different to config

    #inverter output mode priority -> SBU
    if not output_source_priority == b"2":       # 0: Utility first, 1: Solar First, 2: SBU
        ser.flushInput()            #flush input buffer, discarding all its contents
        ser.flushOutput()           #flush output buffer, aborting current output and discard all that is in buffer
        command = "POP02"           # Set to SBU
        print (command)
        xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
        command_crc = command + (unhexlify(hex(xmodem_crc_func(command.encode('utf-8'))).replace('0x','',1))).decode('utf-8', 'ignore') + '\x0d'
        ser.write(command_crc.encode())
        response = ser.readline()
        print (response)

        #delay time
        print ("Delay 10 second")
        time.sleep(10)
    else:
        print ("Output mode no change")

    #inverter charger mode priority -> Solar Only
    if not charger_source_priority == b"3":      # 0: Utility first, 1: Solar First, 2: Solar+Utility, 3: Solar Only
        ser.flushInput()            #flush input buffer, discarding all its contents
        ser.flushOutput()           #flush output buffer, aborting current output and discard all that is in buffer
        command = "PCP03"           # Setting device charger priority: Utility First    
        print (command)
        xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
        command_crc = command + (unhexlify(hex(xmodem_crc_func(command.encode('utf-8'))).replace('0x','',1))).decode('utf-8', 'ignore') + '\x0d'
        ser.write(command_crc.encode())
        response = ser.readline()
        print (response)
    else:
        print ("Charger mode no change")

    ser.close()

except Exception as e:
    text = "error reading inverter...: " + str(e)
    print (text)
    if token != "":
        bot.sendMessage(chat_id=chat_id, text=text)
    exit()
