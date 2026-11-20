# AtmosGear Open Documentation & Reverse-Engineering Notes

> **[English](README.md) | [Español](README.es.md)**

Community-driven technical documentation, factory **VESC v5.02** configuration backups, **Remote AG1 (Flipsky VX1)** protocol analysis, wiring diagrams, and Python diagnostic tools for **AtmosGear electric inline skates**.

Because almost no technical documentation exists publicly for AtmosGear's internal electronics, firmware configuration, or remote control menus, this repository shares verified findings collected directly from live hardware over UART so riders, repairers, and tinkerers can understand, maintain, and safely tune their skates.

---

## Key Findings at a Glance

- **Dual VESC Architecture:** Inside the waist pack are **two STM32F405 VESC controllers** running **VESC Firmware v5.02 (`HW: 410`)**, linked over an internal **500 kbps CAN bus**:
  - **Master ESC:** CAN ID `64`
  - **Slave ESC:** CAN ID `66` (`m_invert_direction = 1` for mirrored wheel rotation)
- **Stock VESC v5.02 Config Schemas:** Exact standard signatures (`MCCONF = 0x83d6207a`, `APPCONF = 0xc29ad144`), Sensorless FOC, **`±22.0 A`** motor current per skate, `0.80 s` accel ramp / `0.40 s` brake ramp, `15%` deadband, `APP_UART` at `115200` baud.
- **Remote AG1 = Flipsky VX1:** Uses a standard Flipsky VX1 UART receiver (`S`/PPM unused) streaming `COMM_SET_CHUCK_DATA` at ~100 Hz with three speed ceilings (**50% / 64% / 100%** forward; **100%** brake in all modes). Micro-USB is **charge-only**.
- **Mystery Blinking Red LEDs Solved:** Holding the left button (~2 s) enters the Flipsky VX1 **6S / 8S / 10S / 12S battery-pack voltage calibration menu** (for the 4 skate-battery LEDs read via the white `V` wire) — it does **not** alter speed or assist modes.
- **Push-Assist Source Isolated:** Sniffing 4,568 live UART frames (including simulated `5000 ERPM` VESC telemetry) proved the Flipsky receiver sends **0** RPM/telemetry requests (`COMM_GET_VALUES`) and `APPCONF` has no PAS enabled — isolating automatic skating push-assist strictly to the **STM32F405 firmware**.

---

## Repository Structure

```text
atmosgear-open-docs/
├── README.md                              # Project overview (English)
├── README.es.md                           # Resumen del proyecto (Español)
├── assets/images/                         # Hardware & receiver pinout photos (EXIF-stripped)
├── configs/
│   ├── README.md                          # Backup format & safety notes
│   └── factory_vesc_5.02/                 # Unmodified factory MCCONF/APPCONF .bin dumps + JSON
├── docs/
│   ├── 01-hardware-architecture.md        # Dual STM32F405 VESC 410, CAN topology, pinouts, teardown
│   ├── 02-vesc-factory-configuration.md   # Complete verified MCCONF & APPCONF diffs vs stock 5.02
│   ├── 03-remote-ag1-flipsky-vx1.md       # Remote AG1 / VX1 modes, 6S–12S LED menu, UART capture
│   ├── 04-raspberry-pi-diagnostics-guide.md # Safe 3.3V wiring + VESC Tool Wi-Fi bridge (socat)
│   ├── 05-push-assist-investigation.md    # Proof isolating push-assist to STM32 firmware + next steps
│   └── GUIA_COMPLETA_ES.md                # Complete technical guide in Spanish
└── tools/
    ├── README.md                          # Tool usage examples
    ├── decode_vesc_conf.py                # Zero-dependency VESC v5.02 .bin decoder & differ
    └── analyze_flipsky.py                 # Flipsky VX1 UART sniffer & fake-VESC simulator
```

---

## Quick Start

### Decode & Diff Factory VESC Backups (No Dependencies)

```bash
# Compare AtmosGear factory APPCONF against stock VESC v5.02 defaults
python3 tools/decode_vesc_conf.py \
  configs/factory_vesc_5.02/default_appconf.bin \
  configs/factory_vesc_5.02/master_appconf.bin

# Compare Master (ID 64) vs Slave (ID 66) motor configs
python3 tools/decode_vesc_conf.py \
  configs/factory_vesc_5.02/master_mcconf.bin \
  configs/factory_vesc_5.02/slave_66_mcconf.bin
```

### Sniff the Flipsky Receiver on a Raspberry Pi

```bash
python3 tools/analyze_flipsky.py --port /dev/serial0 --duration 30 --fake-vesc --erpm 5000
```

---

## Disclaimer & Contributing

This is an **unofficial, independent community documentation project** not affiliated with AtmosGear or Flipsky. Modifying ESC parameters, wiring live lithium battery packs, or flashing firmware carries risk of hardware damage or injury — **always back up your own ESC configurations first** and verify wiring voltages before powering on.

Have PCB photos, firmware observations, VESC Terminal outputs, or corrections? Pull Requests and Issues are very welcome!

## License

- Code & scripts in `tools/`: [MIT License](LICENSE).
- Documentation & photos: feel free to share and build upon with attribution to help the community.
