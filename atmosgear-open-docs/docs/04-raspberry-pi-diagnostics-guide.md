# 04 — Raspberry Pi Diagnostics & VESC Tool Wi-Fi Bridge Guide

You do **not** need a proprietary dongle to inspect, back up, or tune an AtmosGear VESC controller — any **Raspberry Pi** (or 3.3V USB-to-TTL serial adapter) can speak natively to either:
1. **The AtmosGear Dual VESC board** (unplugging the Flipsky receiver from the VESC UART port), or
2. **The Flipsky VX1 receiver standalone** (with the skates completely powered off and disconnected).

---

## Safety First

- **3.3V UART logic only:** Both the STM32F405 VESC UART and the Flipsky VX1 receiver UART (`VRX`/`VTX`) operate at **3.3V TTL**, matching the Raspberry Pi GPIO header.
- **Never connect the white `V` wire** (battery B+, ~24–29.4V) to a Raspberry Pi!
- **Never connect the VESC `5V` wire** to a Raspberry Pi that is already powered via USB — when talking to the VESC board, connect **only `GND`, `TX`, and `RX`** (3 wires).
- **Keep skate wheels elevated** and clear of hands/cables whenever the battery pack is powered on.
- **Always back up both ESCs** (Master CAN ID `64` and Slave CAN ID `66`) before modifying any setting.

---

## 1. Raspberry Pi Setup (Enable Hardware UART)

On Raspberry Pi OS / Kali Linux for Raspberry Pi:

1. Disable the Linux serial login console and enable the hardware UART (`/dev/serial0` → `/dev/ttyS0` or `/dev/ttyAMA0`) via `raspi-config` (Interface Options → Serial Port → Login shell: **No**, Serial hardware: **Yes**) or `/boot/firmware/config.txt` (`enable_uart=1`).
2. Install required utilities:

```bash
sudo apt update
sudo apt install -y python3-serial socat
```

3. Verify `/dev/serial0` exists and your user is in the `dialout` group:

```bash
ls -la /dev/serial0
sudo usermod -aG dialout "$USER"
```

---

## 2. Wiring Option A — Raspberry Pi ↔ AtmosGear VESC Board

Unplug the black Flipsky receiver from the VESC UART header, keep the skates powered from their own battery pack, and connect **only 3 wires** (do **not** connect `5V` or `V`):

| VESC UART Port | Raspberry Pi GPIO Pin |
| :--- | :--- |
| **`GND`** | **Pin 6**, **Pin 9**, or **Pin 14** (`GND`) |
| **`TX`** (VESC out) | **Pin 10** (`GPIO 15 / RXD`) |
| **`RX`** (VESC in) | **Pin 8** (`GPIO 14 / TXD`) |

> **Tip:** If you receive zero bytes at `115200` baud, swap `TX` and `RX` (Pins 8 and 10). Both lines are 3.3V logic and safe to cross-test.

### Wireless VESC Tool Bridge over Wi-Fi (`socat`)

Once the Raspberry Pi is wired to the VESC UART, you can expose the VESC over your local Wi-Fi network on TCP port **`65102`** (the default VESC Tool TCP port) so you can use **VESC Tool** visually from macOS, Windows, Linux, Android, or iOS:

```bash
socat TCP-LISTEN:65102,reuseaddr,fork FILE:/dev/serial0,b115200,raw,echo=0
```

Then open **VESC Tool** (use a version compatible with **VESC Firmware v5.02**), go to **Connection → TCP**, enter your Raspberry Pi's IP address and port **`65102`**, and click **Connect**.

- You will connect directly to **Master ESC (CAN ID `64`)**.
- Use the **CAN Devices** panel in VESC Tool to inspect or configure **Slave ESC (CAN ID `66`)** over the internal CAN bus (`500 kbps`).

---

## 3. Wiring Option B — Raspberry Pi ↔ Flipsky VX1 Receiver (Standalone)

To inspect the remote control safely on your desk with the **skates completely disconnected**, power the Flipsky receiver from the Raspberry Pi's `5V` rail and connect **4 wires**:

```text
      Inner Row (odd)          Outer Row (even / board edge)
Pin 1  [  3.3V  ]             [   5V   ] Pin 2   <-- RED (5V)
Pin 3  [ GPIO 2 ]             [   5V   ] Pin 4   (alt 5V / often used by fans)
Pin 5  [ GPIO 3 ]             [  GND   ] Pin 6   (alt GND / often used by fans)
Pin 7  [ GPIO 4 ]             [  TXD   ] Pin 8   <-- GREEN (VTX)
Pin 9  [  GND   ] <--         [  RXD   ] Pin 10  <-- BLUE (VRX)
       BLACK (-)
Pin 11 [ GPIO17 ]             [ GPIO18 ] Pin 12
Pin 13 [ GPIO27 ]             [  GND   ] Pin 14  (alt GND)
```

| Flipsky Receiver Pin | Wire Color | Raspberry Pi Pin | Notes |
| :---: | :---: | :--- | :--- |
| **`5V`** | Red | **Pin 2** (or Pin 4) | Powers the receiver |
| **`-`** | Black | **Pin 9** (or Pin 6 / 14) | Common GND |
| **`VTX`** | Green | **Pin 8** (`GPIO 14 / TXD`) | Receiver RX ← Pi TX |
| **`VRX`** | Blue | **Pin 10** (`GPIO 15 / RXD`) | Receiver TX → Pi RX |
| **`V`** | White | **DO NOT CONNECT** | Leave insulated / floating |
| **`S`** | *(empty)* | **DO NOT CONNECT** | Unused PPM pin |

Then run the included sniffer & fake-VESC simulator:

```bash
python3 tools/analyze_flipsky.py --port /dev/serial0 --duration 30 --fake-vesc --erpm 5000
```

You should immediately see `COMM_SET_CHUCK_DATA` packets streaming at ~100 Hz as you move the thumbwheel and toggle speed modes.
