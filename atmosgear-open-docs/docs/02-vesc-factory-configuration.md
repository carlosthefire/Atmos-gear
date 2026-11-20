# 02 — VESC v5.02 Factory Configuration (`MCCONF` & `APPCONF`)

All parameters below were decoded directly from the unmodified binary dumps in [`configs/factory_vesc_5.02/`](../configs/factory_vesc_5.02/) using [`tools/decode_vesc_conf.py`](../tools/decode_vesc_conf.py) against the official VESC v5.02 serialization schema (`vedderb/bldc` tag `5.02`).

- **`MCCONF_SIGNATURE`:** `2211848314` (`0x83d6207a`) — 458 bytes (including 1-byte `COMM` header)
- **`APPCONF_SIGNATURE`:** `3264926020` (`0xc29ad144`) — 419 bytes (including 1-byte `COMM` header)

Because both signatures match stock VESC v5.02 identically, standard VESC Tool (matching v5.02) and standard parsers can read and decode these configurations natively.

---

## 1. `APPCONF` — Exact Diff vs. Stock VESC v5.02 Defaults

Out of **149 fields** in `APPCONF`, **only 6 fields** differ from stock VESC v5.02 defaults, and Master (`ID 64`) and Slave (`ID 66`) are identical except for `controller_id`:

| Parameter | Stock Default | Master (ID 64) | Slave (ID 66) | Meaning |
| :--- | :---: | :---: | :---: | :--- |
| `controller_id` | `11` | **`64`** | **`66`** | Unique CAN bus node ID per skate |
| `send_can_status` | `0` (`DISABLED`) | **`4`** (`STATUS_1_2_3_4`) | **`4`** (`STATUS_1_2_3_4`) | Broadcasts ERPM, current, duty, Wh/Ah, and temps over CAN |
| `app_chuk_conf.ramp_time_pos` | `0.40 s` | **`0.80 s`** | **`0.80 s`** | Throttle acceleration smoothing ramp (0 → 100% in 0.8 s) |
| `app_chuk_conf.ramp_time_neg` | `0.20 s` | **`0.40 s`** | **`0.40 s`** | Braking smoothing ramp (0.4 s) |
| `app_chuk_conf.use_smart_rev` | `1` (`True`) | **`0`** (`False`) | **`0`** (`False`) | Smart Reverse explicitly disabled |
| `app_chuk_conf.smart_rev_max_duty` | `0.07` | **`0.0`** | **`0.0`** | Smart Reverse duty zeroed out |

### Other Important `APPCONF` Settings (Unchanged from VESC v5.02 Defaults)

| Parameter | Value | Description |
| :--- | :---: | :--- |
| `app_to_use` | `3` (`APP_UART`) | Control comes strictly over UART (not PPM, ADC, or PAS) |
| `app_uart_baudrate` | `115200` | Standard VESC serial baud rate |
| `can_baud_rate` | `2` (`500 kbps`) | Internal CAN bus speed |
| `send_can_status_rate_hz` | `50` Hz | CAN telemetry broadcast rate |
| `timeout_msec` | `1000` ms | 1 s failsafe timeout if remote signal drops |
| `timeout_brake_current` | `0.0` A | Freewheels (coasts) rather than hard-braking on signal loss |
| `app_chuk_conf.ctrl_type` | `1` (`CURRENT`) | Current control with reverse (throttle forward, brake back, reverse from stop) |
| `app_chuk_conf.hyst` | `0.15` (`15%`) | Center deadband around neutral (`js_y = 128`) |
| `app_chuk_conf.throttle_exp` | `0.0` | Linear throttle curve |
| `app_chuk_conf.throttle_exp_brake` | `0.0` | Linear braking curve |
| `app_chuk_conf.multi_esc` | `1` (`True`) | Forwards UART remote throttle command to the Slave ESC via CAN |
| `app_chuk_conf.tc` | `0` (`False`) | Traction control disabled |
| `app_chuk_conf.tc_max_diff` | `3000.0` ERPM | Default TC ERPM difference threshold (unused while `tc = 0`) |

> **Key observation:** No standard VESC Pedal Assist (`APP_PAS`) or Balance app is enabled in `APPCONF`.

---

## 2. `MCCONF` — Exact Diff vs. Stock VESC v5.02 Defaults

Out of **151 fields** in `MCCONF`, the following parameters differ from stock defaults (or between Master and Slave):

| Parameter | Stock Default | Master (ID 64) | Slave (ID 66) | Notes |
| :--- | :---: | :---: | :---: | :--- |
| `motor_type` | `0` (`BLDC`) | **`2`** (`FOC`) | **`2`** (`FOC`) | Field Oriented Control |
| `foc_sensor_mode` | `0` (`SENSORLESS`) | `0` (`SENSORLESS`) | `0` (`SENSORLESS`) | Runs Sensorless FOC (even though hall table bytes are populated) |
| `l_current_max` | `60.0` A | **`22.0` A** | **`22.0` A** | Max motor acceleration phase current per skate |
| `l_current_min` | `-60.0` A | **`-22.0` A** | **`-22.0` A** | Max regenerative braking current per skate |
| `l_abs_current_max` | `130.0` A | **`150.0` A** | **`150.0` A** | Absolute overcurrent fault trip threshold |
| `l_battery_cut_start` | `10.0` V | **`10.2` V** | **`10.2` V** | Left near 3S default — pack **BMS** handles real 7S LVC |
| `l_battery_cut_end` | `8.0` V | **`9.0` V** | **`9.0` V** | Left near 3S default — pack **BMS** handles real 7S LVC |
| `foc_motor_r` | `0.015` Ω | **`0.1303` Ω** | **`0.1373` Ω** | Measured hub motor phase resistance |
| `foc_motor_l` | `7.0` µH | **`37.11` µH** | **`38.04` µH** | Measured hub motor phase inductance |
| `foc_motor_flux_linkage` | `2.45` mWb | **`7.755` mWb** | **`7.936` mWb** | Measured motor flux linkage |
| `foc_observer_gain` | `90.0 × 10⁶` | **`16.63 × 10⁶`** | **`15.88 × 10⁶`** | Sensorless observer gain |
| `foc_current_kp` | `0.0300` | **`0.0371`** | **`0.0380`** | FOC current controller proportional gain |
| `foc_current_ki` | `50.0` | **`130.34`** | **`137.27`** | FOC current controller integral gain |
| `foc_openloop_rpm` | `1500` ERPM | **`1400` ERPM** | **`1400` ERPM** | Open-loop startup RPM |
| `foc_sl_erpm` | `2500` ERPM | **`4000` ERPM** | **`4000` ERPM** | Sensorless transition ERPM |
| `foc_hall_table[1..6]` | `255` (all) | **`116, 52, 83, 182, 151, 16`** | **`116, 52, 83, 182, 151, 16`** | Populated hall table (inactive because `foc_sensor_mode = 0`) |
| `m_invert_direction` | `0` (`False`) | **`0`** (`False`) | **`1`** (`True`) | Slave skate hub motor is physically mirrored |
| `si_gear_ratio` | `3.0` | **`2.7692`** (`36/13`) | **`2.7692`** (`36/13`) | Telemetry ratio (note: hub motor is direct-drive `1.0`) |
| `si_battery_ah` | `6.0` Ah | **`60.0` Ah** | **`60.0` Ah** | Telemetry battery Ah field |

### Other Notable `MCCONF` Limits (Unchanged Defaults)

- **`l_in_current_max` / `l_in_current_min`:** `+99.0 A` / `-60.0 A` (battery current effectively limited by motor current `±22 A` and duty cycle)
- **`l_max_duty`:** `0.95` (`95%`)
- **`l_max_erpm` / `l_min_erpm`:** `±100,000` ERPM (no artificial ERPM speed cap in `MCCONF`)
- **`l_temp_fet_start` / `l_temp_fet_end`:** `85 °C` (start thermal throttling) / `100 °C` (cutoff)
- **`si_motor_poles` / `si_wheel_diameter` / `si_battery_cells`:** `14` poles / `0.083 m` (`83 mm`) / `3` cells (left at stock VESC Tool defaults; physical AtmosGear wheels are typically `110 mm` and battery is ~`7S`, so VESC internal speed/distance/battery-% calculations are not calibrated from `MCCONF`).

---

## 3. Useful Safe Tuning Ideas (via VESC Tool)

If you connect VESC Tool over UART or a Raspberry Pi TCP bridge (always back up first!):

- **Snappier throttle response:** Lower `app_chuk_conf.hyst` from `0.15` (15%) to `0.05–0.08` and reduce `app_chuk_conf.ramp_time_pos` from `0.80 s` to `0.30–0.45 s`.
- **Disable accidental reverse while braking:** Change `app_chuk_conf.ctrl_type` from `1` (`Current`) to `2` (`Current No Reverse`).
- **Prevent a lifted skate from free-spinning away:** Enable `app_chuk_conf.tc = True` (Traction Control).
- **Adjust torque / brake strength:** Tune `l_current_max` / `l_current_min` (factory is `±22 A` per skate). Remember to apply `MCCONF` and `APPCONF` changes to **both** CAN ID `64` and CAN ID `66`.
