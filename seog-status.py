#!/usr/bin/env python3

import serial
import datetime

now = datetime.datetime.now()
print(now)

# Hardcoded to the device name that was assigned when I plugged in the
# serial-to-USB cable.

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.write(b'A')
s = ser.readline()
ser.close()

print("<<< " + s.hex())

# Here's the example/explanation from Statcon Energiaa technical support:
#
# Computer:  A
# Inverter: 52 46 08 FD 00 00 01 CF 00 29 00 00 00 00 00 00 12 3D 2E 00 00 00 00
# 00 6E 79 42 6E 6E 6E 6E 6E 6E 6E 79 6E 6E
#
# 1st Byte in Hex=52              (Inverter status)
# 2nd Byte in Hex=46              (Load on)
# 3rd &4th Byte in Hex=08 FD      (AC Voltage)
# 5th &6th Byte in Hex=00 00      (AC Current)
# 7&8th Byte in Hex=01 CF         (Battery Voltage)
# 9&10th Byte in Hex=00 29        (Battery current)
# 11&12th Byte in Hex=00 00       (PV Voltage)
# 13&14th Byte in Hex=00 00       (PV Current)
# 15&16th Byte in Hex=00 00       (Solar I/P Power)
# 17&18th Byte in Hex=12 3D       (Todays Solar kWH)
# 19-22 Byte in Hex=2E 00 00 00   (Total Solar kWH_1 & Total Solar kWH_2 )
# 23&24 Byte in Hex=00 00         (Monthly Solar kWH(Solar))
# 25th Byte in Hex=6E             (System Fault)
# 26th Byte in Hex=79             (Battery status)
# 27th Byte in Hex=42             (charging status)
# 28th Byte in Hex=6E             (Inverter UV)
# 29th Byte in Hex=6E             (Inverter OV)
# 30 Byte in Hex=6E               (Battrey UV)
# 31 Byte in Hex=6E               (Battery OV)
# 32 Byte in Hex=6E               (System Over Tempreture)
# 33 Byte in Hex=6E               (TCS Fail)
# 34 Byte in Hex=6E               (PV OV)
# 35 Byte in Hex=79               (PV UV)
# 36 Byte in Hex=6E               (System Over Load)
# 37 Byte in Hex=6E               (System Switched)

status = chr(s[0])
print(f"Inverter status: {status}")

# 'B' means the load is on the grid (bypassing the inverter).
#
# 'F' means the load is on battery (at least) and/or solar (unsure).

load = chr(s[1])
print(f"Load on: {load}")

# The AC voltage and current reported appear to be the inverter's output voltage
# and current, i.e., correlated with the load on the inverter. If the load is on
# the grid, bypassing the inverter, these values are close to 0.

ac_voltage = int(s[2:4].hex(), 16) / 10
print(f"AC voltage: {ac_voltage}V")

ac_current = int(s[4:6].hex(), 16) / 10
print(f"AC current: {ac_current}A")

bat_voltage = int(s[6:8].hex(), 16) / 10
print(f"Battery voltage: {bat_voltage}V")

# The current is reported as an absolute value, whether the battery is charging
# or discharging. We interpret the value as negative if "battery status" is 'y'
# (I expected "charging status" to be the field that determines the sign, but
# it's only "battery status" that I've seen vary so far.)

bat_current = int(s[8:10].hex(), 16) / 10
if len(s) >= 24:
    bat_status = chr(s[25])
    if bat_status == 'y':
        bat_current *= -1
print(f"Battery current: {bat_current}A")

pv_voltage = int(s[10:12].hex(), 16) / 10
print(f"PV voltage: {pv_voltage}V")

pv_current = int(s[12:14].hex(), 16) / 10
print(f"PV current: {pv_current}A")

pv_power = int(s[14:16].hex(), 16) / 1000
print(f"PV power: {pv_power}kW")

pv_units = int(s[16:18].hex(), 16) / 1000
print(f"PV units today: {pv_units:.2f}kWh")

# I'm just guessing at the right scale for the total kWh field.

pv_total = int(s[18:22].hex(), 16) / 10_000_000
print(f"PV units total: {pv_total:.2f}kWh (uncertain)")

# The values I've seen reported for this field seem inconsistent, so I'm
# probably not decoding it correctly here.

pv_month = int(s[22:24].hex(), 16) / 1000
print(f"PV units this month: {pv_month}kWh (uncertain)")

fault = chr(s[24])
if fault != 'n':
    print(f"System fault: {fault}")

bat_status = chr(s[25])
print(f"Battery status: {bat_status}")

charging_status = chr(s[26])
print(f"Charging status: {charging_status}")

# I speculate that the following fields all toggle between 0x6E ('n') and 0x79
# ('y'), but I don't know for sure. It does work that way for PV under-voltage,
# at least.

inverter_uv = chr(s[27])
if inverter_uv != 'n':
    print(f"Inverter under voltage: {inverter_uv}")

inverter_ov = chr(s[28])
if inverter_ov != 'n':
    print(f"Inverter over voltage: {inverter_ov}")

battery_uv = chr(s[29])
if battery_uv != 'n':
    print(f"Battery under voltage: {battery_uv}")

battery_ov = chr(s[30])
if battery_ov != 'n':
    print(f"Battery over voltage: {battery_ov}")

overheating = chr(s[31])
if overheating != 'n':
    print(f"System overheating: {overheating}")

tcs_fail = chr(s[32])
if tcs_fail != 'n':
    print(f"TCS fail: {tcs_fail}")

pv_ov = chr(s[33])
if pv_ov != 'n':
    print(f"PV over voltage: {pv_ov}")

pv_uv = chr(s[34])
if pv_uv != 'n':
    print(f"PV under voltage: {pv_uv}")

overload = chr(s[35])
if overload != 'n':
    print(f"System overload: {overload}")

# What does this mean? I thought it was "system switched on", but then it
# shouldn't be returning 'n'.

switched = chr(s[36])
if switched != 'n':
    print(f"System switched: {switched}")
