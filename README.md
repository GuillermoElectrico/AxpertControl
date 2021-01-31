# AxpertControl
Controling Software for Axpert Inverter

Repository contains:

axpert_valle.py
Python script communicate with Axpert inverter and switch mode to electric low tarif

axpert_pico.py
Python script communicate with Axpert inverter and switch mode to electric high tarif

axpert_tmp.py
testing script wiht CRC, commands, ...�

Crontab example:

*/15 0-11,22,23 * * * /home/pi/AxpertControl/axpert_valle.py >/dev/null 2>&1

*/15 12-21 * * * /home/pi/AxpertControl/axpert_pico.py >/dev/null 2>&1

Tested and running in PIP-5048MK 

If the error appears, use dos2unix to fix it.

 $ sudo apt install dos2unix
 $ dos2unix /PATH/TO/YOUR/FILE

Example to spain tarif:

# For more information see the manual pages of crontab(5) and cron(8)
#
# m h  dom mon dow   command

# Horario Verano:

*/15 0-12,23 * * * /home/pi/AxpertControl/axpert_valle.py >/dev/null 2>&1

*/15 13-22 * * * /home/pi/AxpertControl/axpert_pico.py >/dev/null 2>&1

# Horario Invierno:

#*/15 0-11,22,23 * * * /home/pi/AxpertControl/axpert_valle.py >/dev/null 2>&1

#*/15 12-21 * * * /home/pi/AxpertControl/axpert_pico.py >/dev/null 2>&1

# Actualización (31/01/2021)
# ¡¡¡ Ejemplo crontab para la nueva tarifa 2.0TD en españa !!! https://selectra.es/energia/info/que-es/tarifa-20-td

*/15 0-7 * * 1-5 /home/pi/AxpertControl/axpert_valle.py >/dev/null 2>&1

*/15 8-23 * * 1-5 /home/pi/AxpertControl/axpert_pico.py >/dev/null 2>&1

*/15 * * * 6,0 /home/pi/AxpertControl/axpert_valle.py >/dev/null 2>&1

26/01/2020 - Migrate code to Python 3
