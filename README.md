# Monitoring an SEOG solar PCU

The
[Statcon Energiaa SEOG off-grid solar PCU](https://www.energiaa.in/off-grid-solar-pcu/)
has a serial port on the back, and it doesn't take much effort to read
some monitoring data from it.

I wrote some code to decode the PCU's status, based on example data that
Statcon technical support provided on request.

I run this on a Raspberry Pi that's connected to the PCU's serial port
using a random serial-to-USB cable:

    pi@shikra:~ $ lsusb -s 1:4
    Bus 001 Device 004: ID 1a86:7523 QinHeng Electronics CH340 serial converter

The code works well enough that I prefer it to climbing up a ladder to
the battery room to read the machine's tiny display (which is admittedly
not a very high bar). The interpretation of a few fields is not entirely
clear; see below.

## Example output

    pi@shikra:~ $ ~/seog-status.py
    2024-12-19 17:55:25.187134
    <<< 524608f8000901f10063004f0000000028421501000007c66e79426e6e6e6e6e6e6e796e6e
    Inverter status: R
    Load on: F
    AC voltage: 229.6V
    AC current: 0.9A
    Battery voltage: 49.7V
    Battery current: -9.9A
    PV voltage: 7.9V
    PV current: 0.0A
    PV power: 0.0kW
    PV units today: 10.306kWh
    PV units total: 35.24kWh (scale guessed)
    PV units this month: 1.99kWh (uncertain)
    Battery status: y
    Charging status: B
    PV under voltage: y

## Open questions

- The battery current is reported as an absolute value. How does one
  know if it's positive (charging) or negative (discharging)? I hoped
  the "charging status" would tell me, but it only shows "B" so far.

- Is there any way to get the current load? The display does report a
  percentage and "Load on solar", so it should be possible.

- I don't know how to decode the monthly cumulative total PV generation
  value.

## Compatibility

I run this code against a 5kVA/48V PCU (SEOG-048-5K0-1P). I imagine it
would work with other models of Statcon Energiaa inverters, but I don't
know for sure.

## License

Released under the MIT license.
