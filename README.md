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

*/15 0-12,22,23 * * * /home/pi/AxpertControl/axpert_valle.py > /tmp/axpert_valle.log 2>&1

*/15 12-21 * * * /home/pi/AxpertControl/axpert_pico.py > /tmp/axpert_pico.log 2>&1
