# 05 — Investigation: Automatic Skating Push-Assist ("Smart Assist")

## Problem Statement

Some AtmosGear riders want the skates to behave strictly in **manual throttle mode** (freewheeling 100% when skating on muscle power, and only applying motor torque when pressing the remote thumbwheel). When an automatic stride/speed push-assist engages while skating manually, it can accelerate the motorized center wheels unexpectedly, causing extra wheel scrubbing and premature wear.

---

## Hypothesis Testing & Ruled-Out Causes

During our reverse-engineering session, we tested all three places where automatic push-assist could live:

### 1. Standard VESC `APPCONF` / `MCCONF` Parameters — **RULED OUT**
- Diffing `master_appconf.bin` and `slave_66_appconf.bin` against stock VESC v5.02 defaults (`default_appconf.bin`) shows **only 6 changed fields**: `controller_id`, `send_can_status`, `ramp_time_pos`, `ramp_time_neg`, `use_smart_rev`, and `smart_rev_max_duty`.
- `app_to_use` is `3` (`APP_UART`). Neither Pedal Assist (`APP_PAS`) nor Balance mode is enabled.
- `MCCONF` (`master_mcconf.bin` / `slave_66_mcconf.bin`) contains only standard FOC motor detection constants, `±22 A` current limits, and `m_invert_direction = 1` on Slave ID `66`.

### 2. Flipsky VX1 Receiver & Remote AG1 — **RULED OUT**
- Connecting the black Flipsky receiver directly to a Raspberry Pi (`tools/analyze_flipsky.py --fake-vesc --erpm 5000`) and sniffing **4,568 continuous packets across 45 seconds** proved:
  - The receiver emits **only** `COMM_SET_CHUCK_DATA` (`0x23`) at ~100 Hz.
  - The receiver sent **0 telemetry requests** (`COMM_GET_VALUES` = `0`, `COMM_GET_VALUES_SELECTIVE` = `0`).
  - `bt_c` (Cruise Control) and `bt_z` stayed `0` across all tests.
- Because the receiver never reads motor ERPM from the VESC, **neither the receiver nor the Remote AG1 can detect skating speed or trigger push-assist**.

### 3. Custom Logic Inside the STM32F405 VESC v5.02 Firmware — **REMAINING LOCATION**
- Both ESCs report VESC v5.02 (`HW: 410`) with stock configuration signatures (`0x83d6207a` / `0xc29ad144`), and notably have `send_can_status = 4` (`CAN_STATUS_1_2_3_4` @ 50 Hz) enabled on both Master (`ID 64`) and Slave (`ID 66`), allowing both ESCs to continuously observe each other's ERPM over CAN.
- Therefore, any automatic skating push-assist behavior is implemented inside the **compiled STM32F405 firmware** itself (e.g., custom logic inside `app_nunchuk.c` or a custom thread reading wheel ERPM / CAN status).

---

## Recommended Next Steps for Community Research

If you want to investigate further or permanently disable firmware-level push-assist:

1. **Bench Spin Test (Receiver Unplugged):**
   - Disconnect the Flipsky receiver from the VESC UART port and connect a Raspberry Pi running a live `COMM_GET_VALUES` monitor (`erpm`, `current_motor`, `duty_now`).
   - Spin the motorized wheel(s) rapidly by hand with the skates powered on and check whether `current_motor` jumps above `0 A` automatically once ERPM exceeds a threshold (testing both single-wheel spin and dual-wheel spin in case the firmware checks both CAN IDs `64` and `66`).
2. **Inspect VESC Terminal Commands (`COMM_TERMINAL_CMD`):**
   - Query `help` over VESC Tool's **VESC Terminal** (or via Python UART) to check whether AtmosGear registered any custom CLI command or toggle for Smart Assist without needing a firmware reflash.
3. **Full SWD Flash Backup Before Any Reflash:**
   - **CRITICAL:** Before ever flashing stock official VESC v5.02 (`HW: 410`) firmware onto the STM32F405 chips, verify the exact physical ESC PCB (shunt resistor values, voltage divider, power switch circuitry) and dump the original STM32 flash via SWD (`OpenOCD` / ST-Link) if possible, since VESC UART does not support reading back compiled flash binaries.
   - If hardware is confirmed 100% standard VESC `410` (e.g., Flipsky Dual FSESC 4.20), flashing clean official VESC v5.02 `410` firmware to both CAN ID `64` and `66` and restoring the motor calibration (`master_mcconf.bin`, `slave_66_mcconf.bin`, and `appconf`) would give 100% stock VESC manual-remote-only behavior.

Contributions, PCB photos, terminal outputs, and bench test results are welcome via Pull Requests or Issues!
