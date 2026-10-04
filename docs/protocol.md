# Protocol notes

This file documents only the subset currently implemented from the supplied MDROBOT RS485/RS232 communication manual.

## Frame

```text
RMID | TMID | ID | PID | DataNumber | DATA... | CHK
```

For PC/MMI -> motor driver:

- RMID = 183 / 0xB7
- TMID = 172 / 0xAC
- ID = driver ID (0..253)
- broadcasting ID = 254 / 0xFE
- multi-byte values are low-byte first

A read request uses PID 4:

```text
B7 AC ID 04 01 RequestedPID CHK
```

The driver response reverses machine IDs:

```text
AC B7 ID RequestedPID N DATA... CHK
```

## Checksum

```text
CHK = two_complement(sum(RMID..DATA))
```

The full packet byte sum including CHK must be 0 modulo 256.

## Serial default

- 19200 baud
- 8 data bits
- 1 stop bit
- no parity

## Implemented PIDs

| PID | Hex | Name | Type | Purpose |
|---:|---:|---|---|---|
| 1 | 01 | PID_VER | R | firmware/program version |
| 4 | 04 | PID_REQ_PID_DATA | C | request one PID |
| 5 | 05 | PID_TQ_OFF | C | free stop |
| 17 | 11 | PID_USE_LIMIT_SW | R/W | communication-drive limit input behavior |
| 21 | 15 | PID_HALL_TYPE | R/W | Motor 1 Hall pole setup |
| 25 | 19 | PID_INPUT_TYPE | R/W | control input type |
| 65 | 41 | PID_HALL2_TYPE | R/W | Motor 2 Hall pole setup |
| 121 | 79 | PID_MAX_RPM1 | R/W | Motor 1 max rpm |
| 122 | 7A | PID_MAX_RPM2 | R/W | Motor 2 max rpm |
| 130 | 82 | PID_VEL_CMD | C | Motor 1 signed-rpm command |
| 131 | 83 | PID_VEL_CMD2 | C | Motor 2 signed-rpm command |
| 149 | 95 | PID_RETURN_TYPE | R/W | command return-data mode |
| 156 | 9C | PID_ENC_PPR | R/W | encoder pulse setting |
| 193 | C1 | PID_MAIN_DATA | R | Motor 1 main data |
| 196 | C4 | PID_MONITOR | R | Motor 1 monitor |
| 200 | C8 | PID_MAIN_DATA2 | R | Motor 2 main data |
| 201 | C9 | PID_MONITOR2 | R | Motor 2 monitor |

## PID 196 / 201 monitor decode

- D0,D1: RPM
- D2,D3: current, 0.1 A/bit
- D4,D5: controller output
- D6: state bit field
- D7..D10: motor position
- D11: digital input, when present

## MDH250 profile mapping

The MDH250 manual specifies 30 poles, 4096 PPR, 200 rpm rated speed, and 300 rpm max speed.

For Hall pole settings outside the protocol's special lookup values, the communication manual says to use half the pole count:

```text
30 poles -> DATA 15
```

The application applies 15 to PID 21 and PID 65.

Encoder resolution is shown as 4096 PPR, but the communication manual uses PPR/CPR wording inconsistently around encoder parameters. For that reason PID 156 is readable and visible in the app, but the default profile apply operation does not write 4096 automatically.
