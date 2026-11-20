# Factory VESC v5.02 Configuration Backups

This directory contains unmodified binary configuration backups extracted directly via UART (`115200` baud) from a factory dual-ESC AtmosGear electric inline skate unit running **VESC Firmware v5.02 (`HW: 410`)**.

## Files (`factory_vesc_5.02/`)

| File | Size | VESC Command | Signature | Description |
| :--- | :---: | :--- | :--- | :--- |
| `master_mcconf.bin` | 458 B | `COMM_GET_MCCONF` (`0x0e`) | `0x83d6207a` | Factory motor config — Master ESC (**CAN ID 64**) |
| `master_appconf.bin` | 419 B | `COMM_GET_APPCONF` (`0x11`) | `0xc29ad144` | Factory app config — Master ESC (**CAN ID 64**) |
| `slave_66_mcconf.bin` | 458 B | `COMM_GET_MCCONF` (`0x0e`) | `0x83d6207a` | Factory motor config — Slave ESC (**CAN ID 66**) |
| `slave_66_appconf.bin` | 419 B | `COMM_GET_APPCONF` (`0x11`) | `0xc29ad144` | Factory app config — Slave ESC (**CAN ID 66**) |
| `default_mcconf.bin` | 458 B | `COMM_GET_MCCONF_DEFAULT` (`0x0f`) | `0x83d6207a` | Firmware built-in default `MCCONF` |
| `default_appconf.bin` | 419 B | `COMM_GET_APPCONF_DEFAULT` (`0x12`) | `0xc29ad144` | Firmware built-in default `APPCONF` |
| `decoded_summary.json` | 33 KB | — | — | All 6 files decoded to human-readable JSON via `tools/decode_vesc_conf.py` |

## Important Warnings

> **WARNING — Do not flash motor calibration blindly across different hardware units.**  
> Notice that `master_mcconf.bin` and `slave_66_mcconf.bin` contain per-motor FOC detection constants (`foc_motor_r`, `foc_motor_l`, `foc_motor_flux_linkage`, `foc_observer_gain`, `foc_current_kp`, `foc_current_ki`) measured for the specific hub motors of this unit, and `slave_66_mcconf.bin` has `m_invert_direction = 1` (mirrored rotation). Always back up your own ESCs first and run FOC motor detection if replacing firmware or motors.

> **NOTE — Binary format.**  
> Each `.bin` file stores the raw VESC packet payload starting with the 1-byte `COMM_PACKET_ID` (`0x0e`, `0x0f`, `0x11`, `0x12`), followed by the 4-byte big-endian configuration signature (`0x83d6207a` for `MCCONF` or `0xc29ad144` for `APPCONF`) and the serialized VESC v5.02 struct bytes. Use `tools/decode_vesc_conf.py` to inspect or diff them.
