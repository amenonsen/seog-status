#!/usr/bin/env python3

import sys
import time
import serial
import argparse
import datetime

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

def parse(s):
    d = {}

    # Status: 'R'unning or 'I'nactive

    if len(s) >= 1:
        d['status'] = chr(s[0])

    # 'B' means the load is on the grid (bypassing the inverter).
    # 'F' means the load is on battery and/or solar.

    if len(s) >= 2:
        d['load'] = chr(s[1])

    # The AC voltage and current reported appear to be the inverter's output
    # voltage and current, i.e., correlated with the load on the inverter. When
    # the load is on the grid, bypassing the inverter, these values represent
    # the power drawn from the grid for charging.

    if len(s) >= 4:
        d['ac_voltage'] = int(s[2:4].hex(), 16) / 10

    if len(s) >= 6:
        d['ac_current'] = int(s[4:6].hex(), 16) / 10

    # The current is reported as an absolute value, whether the battery is
    # charging or discharging. We make this value negative if the "battery
    # status" is 'y'. (I expected "charging status" to be the field that
    # determines the sign, but I have seen only "battery status" varying.)

    if len(s) >= 8:
        d['bat_voltage'] = int(s[6:8].hex(), 16) / 10

    if len(s) >= 10:
        d['bat_current'] = int(s[8:10].hex(), 16) / 10

    if len(s) >= 12:
        d['pv_voltage'] = int(s[10:12].hex(), 16) / 10

    if len(s) >= 14:
        d['pv_current'] = int(s[12:14].hex(), 16) / 10

    if len(s) >= 16:
        d['pv_power'] = int(s[14:16].hex(), 16)

    # I'm just guessing at the right scale for the total kWh field. (The values
    # I've seen reported for total/month seem inconsistent, so I'm probably not
    # decoding it correctly here.)

    if len(s) >= 18:
        d['pv_units'] = int(s[16:18].hex(), 16) / 1000

    if len(s) >= 22:
        d['pv_total'] = int(s[18:22].hex(), 16) / 10_000_000

    if len(s) >= 24:
        d['pv_month'] = int(s[22:24].hex(), 16) / 1000

    if len(s) >= 25:
        d['fault'] = chr(s[24])

    if len(s) >= 26:
        d['bat_status'] = chr(s[25])
        if d['bat_status'] == 'y':
            d['bat_current'] *= -1

    if len(s) >= 27:
        d['charging_status'] = chr(s[26])

    # The following fields all toggle between 0x6E ('n') and 0x79 ('y').

    fields = [
        'inverter_uv', 'inverter_ov', 'battery_uv', 'battery_ov', 'overheating', 'tcs_fail', 'pv_ov', 'pv_uv', 'overload', 'switched_off',
    ]

    i = 27
    for f in fields:
        if len(s) >= i+1:
            d[f] = chr(s[i])
        i += 1

    return d

def print_verbose_desc(s, d):
    print(">>>", datetime.datetime.now())
    print("<<<", s.hex())

    status = d['status']
    if status == 'R':
        status = 'R (running)'
    elif status == 'I':
        status = 'I (inactive)'
    print(f"Inverter status: {status}")

    load = d['load']
    if load == 'B':
        load = 'B (grid)'
    elif load == 'F':
        if d.get('bat_status', 'n') == 'y':
            load = 'F (battery)'
        else:
            load = 'F (solar)'
    print(f"Load on: {load}")

    print(f"AC voltage: {d['ac_voltage']}V")
    print(f"AC current: {d['ac_current']}A")
    print(f"Battery voltage: {d['bat_voltage']}V")
    print(f"Battery current: {d['bat_current']}A")
    print(f"PV voltage: {d['pv_voltage']}V")
    print(f"PV current: {d['pv_current']}A")
    print(f"PV power: {d['pv_power']}W")
    print(f"PV units today: {d['pv_units']:.2f}kWh")
    print(f"PV units total: {d['pv_total']:.2f}kWh (uncertain)")
    print(f"PV units this month: {d['pv_month']}kWh (uncertain)")
    print(f"Battery status: {d['bat_status']}")
    print(f"Charging status: {d['charging_status']}")

    flags = {
        'fault': "System fault",
        'inverter_uv': "Inverter under voltage",
        'inverter_ov': "Inverter over voltage",
        'battery_uv': "Battery under voltage",
        'battery_ov': "Battery over voltage",
        'overheating': "System overheating",
        'tcs_fail': "TCS fail",
        'pv_ov': "PV over voltage",
        'pv_uv': "PV under voltage",
        'overload': "System overload",
    }

    for f in flags.keys():
        v = d.get(f, 'n')
        if v != 'n':
            print(f"{flags[f]}: {v}")

    if d.get('switched_off', 'n') == 'y':
        print(f"Inverter switched off: y")

def short_desc(s, d):
    l = f"status={d.get('status', '?')}/{d.get('load', '?')}/{d.get('bat_status','?')}/{d.get('charging_status', '?')}"

    l += f", AC=("
    if 'ac_voltage' in d:
        l += f"{d['ac_voltage']:5.1f}V"
    else:
        l += f"  ?.?V"

    l += "; "
    if 'ac_current' in d:
        l += f"{d['ac_current']:4.1f}A"
    else:
        l += f" ?.?A"
    l += f")"

    l += f", BAT=("
    if 'bat_voltage' in d:
        l += f"{d['bat_voltage']:4.1f}V"
    else:
        l += f" ?.?V"

    l += "; "
    if 'bat_current' in d:
        l += f"{d['bat_current']:5.1f}A"
    else:
        l += f"  ?.?A"
    l += f")"

    l += f", PV=("
    if 'pv_voltage' in d:
        l += f"{d['pv_voltage']:5.1f}V"
    else:
        l += f"  ?.?V"

    l += "; "
    if 'pv_current' in d:
        l += f"{d['pv_current']:4.1f}A"
    else:
        l += f" ?.?A"

    l += "; "
    if 'pv_power' in d:
        l += f"{d['pv_power']:4.0f}W"
    else:
        l += f" ???W"

    l += "; "
    if 'pv_units' in d:
        l += f"{d['pv_units']:5.2f}kWh"
    else:
        l += f"??.??kWh"
    l += f")"

    flags = [
        'fault', 'inverter_uv', 'inverter_ov', 'battery_uv', 'battery_ov',
        'overheating', 'tcs_fail', 'pv_ov', 'pv_uv', 'overload'
    ]
    for f in flags:
        v = d.get(f, 'n')
        if v != 'n':
            l += f", {f}={v}"

    if d.get('switched_off', 'n') == 'y':
        l += f", switch=off"

    if len(s) < 37:
        l += f", short_read={len(s)}"

    return l

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        prog='seog-status',
    )

    p.add_argument(
        '-d', '--device',
        default='/dev/ttyUSB0',
        help="Read data from the given serial device"
    )

    p.add_argument(
        '-s', '--short',
        action='store_true',
        help="Produce single-line output"
    )

    p.add_argument(
        '-r', '--repeat',
        type=int,
        metavar="nsecs",
        help="Repeat indefinitely after every <nsecs> seconds",
    )

    p.add_argument(
        '-t', '--timestamp',
        action='store_true',
        help="Display timestamps before each output description"
    )

    args = p.parse_args()

    ser = serial.Serial(args.device, 9600, timeout=2)

    while True:
        ser.write(b'A')
        s = ser.read_until(size=37)

        data = parse(s)

        if args.short:
            if args.timestamp:
                now = "[" + str(datetime.datetime.now()) + "]"
                print(now, short_desc(s, data))
            else:
                print(short_desc(s, data))
        else:
            print_verbose_desc(s, data)

        if not args.repeat:
            break

        sys.stdout.flush()
        time.sleep(args.repeat)

    ser.close()
