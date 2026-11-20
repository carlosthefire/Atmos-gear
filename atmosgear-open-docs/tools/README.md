# Diagnostic & Analysis Tools

This folder contains lightweight Python 3 scripts developed to inspect AtmosGear VESC configuration dumps and analyze the Flipsky VX1 / Remote AG1 UART protocol.

---

## 1. `decode_vesc_conf.py` — VESC v5.02 Binary Config Decoder & Differ

Decodes raw VESC v5.02 `MCCONF` (`0x83d6207a`) and `APPCONF` (`0xc29ad144`) binary backups into human-readable parameters or JSON, and compares two backups field by field.

**Requirements:** Python 3.8+ (standard library only, **no external packages needed**).

### Examples

```bash
# Decode a single config file
python3 tools/decode_vesc_conf.py configs/factory_vesc_5.02/master_appconf.bin

# Diff factory APPCONF against stock VESC 5.02 defaults
python3 tools/decode_vesc_conf.py \
  configs/factory_vesc_5.02/default_appconf.bin \
  configs/factory_vesc_5.02/master_appconf.bin

# Diff Master (ID 64) vs Slave (ID 66) motor configurations
python3 tools/decode_vesc_conf.py \
  configs/factory_vesc_5.02/master_mcconf.bin \
  configs/factory_vesc_5.02/slave_66_mcconf.bin

# Export multiple dumps to JSON
python3 tools/decode_vesc_conf.py --json configs/factory_vesc_5.02/*.bin > summary.json
```

---

## 2. `analyze_flipsky.py` — Flipsky VX1 / Remote AG1 UART Sniffer & Fake VESC

Listens on a 3.3V UART port (e.g., Raspberry Pi `/dev/serial0` at `115200` baud) connected to the Flipsky receiver (`VRX`/`VTX`), decodes every VESC frame live, and can optionally respond as a simulated VESC v5.02 (`--fake-vesc`) with custom ERPM and battery voltage.

**Requirements:** Python 3.8+ and `pyserial`:

```bash
sudo apt install python3-serial
# or
pip install pyserial
```

### Examples

```bash
# Passive sniff for 30 seconds on Raspberry Pi UART
python3 tools/analyze_flipsky.py --port /dev/serial0 --duration 30

# Emulate a VESC v5.02 spinning at 5000 ERPM (~27.1 V battery)
python3 tools/analyze_flipsky.py \
  --port /dev/serial0 \
  --duration 35 \
  --fake-vesc \
  --erpm 5000 \
  --vin 27.1

# Print raw hex chunks in addition to decoded VESC frames
python3 tools/analyze_flipsky.py --port /dev/serial0 --duration 10 --raw
```
