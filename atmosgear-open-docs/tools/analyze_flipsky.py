#!/usr/bin/env python3
"""
Flipsky VX1 / AtmosGear Remote AG1 UART Sniffer & Fake-VESC Simulator.

Connects to a Flipsky VX1 receiver over 3.3V UART (115200 baud) to:
  1. Decode every outgoing VESC packet in real time (e.g., COMM_SET_CHUCK_DATA,
     throttle js_y, speed mode limits, Cruise Control bt_c, Reverse bt_z).
  2. Optionally emulate a VESC v5.02 controller (--fake-vesc) replying to
     COMM_GET_VALUES / COMM_GET_VALUES_SELECTIVE with configurable ERPM and
     battery voltage to test whether the receiver reacts to wheel speed.

Requires: pyserial (`pip install pyserial` or `sudo apt install python3-serial`)
"""

import argparse
import serial
import struct
import time

CMD_NAMES = {
    0: "COMM_FW_VERSION",
    4: "COMM_GET_VALUES",
    5: "COMM_SET_DUTY",
    6: "COMM_SET_CURRENT",
    7: "COMM_SET_CURRENT_BRAKE",
    8: "COMM_SET_RPM",
    9: "COMM_SET_POS",
    10: "COMM_SET_HANDBRAKE",
    12: "COMM_SET_SERVO_POS",
    13: "COMM_SET_MCCONF",
    14: "COMM_GET_MCCONF",
    16: "COMM_SET_APPCONF",
    17: "COMM_GET_APPCONF",
    29: "COMM_ALIVE",
    34: "COMM_FORWARD_CAN",
    35: "COMM_SET_CHUCK_DATA",
    36: "COMM_CUSTOM_APP_DATA",
    48: "COMM_SET_MCCONF_TEMP",
    49: "COMM_SET_MCCONF_TEMP_SETUP",
    50: "COMM_GET_VALUES_SELECTIVE",
    51: "COMM_GET_VALUES_SETUP",
    52: "COMM_GET_VALUES_SETUP_SELECTIVE",
    65: "COMM_GET_DECODED_CHUK",
}


def crc16_vesc(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def build_vesc_packet(payload: bytes) -> bytes:
    n = len(payload)
    hdr = bytes([2, n]) if n <= 255 else bytes([3, (n >> 8) & 0xFF, n & 0xFF])
    crc = crc16_vesc(payload)
    return hdr + payload + struct.pack(">H", crc) + b"\x03"


def build_fake_get_values(
    erpm=0, v_in=27.1, current_motor=0.0, current_in=0.0, duty=0.0, tach=0
):
    """Build a VESC v5.02 COMM_GET_VALUES response frame."""
    p = bytearray()
    p.append(4)  # COMM_GET_VALUES
    p += struct.pack(">h", int(30.0 * 10))          # temp_fet
    p += struct.pack(">h", int(28.0 * 10))          # temp_motor
    p += struct.pack(">i", int(current_motor * 100))
    p += struct.pack(">i", int(current_in * 100))
    p += struct.pack(">i", 0)                       # id
    p += struct.pack(">i", 0)                       # iq
    p += struct.pack(">h", int(duty * 1000))        # duty_now
    p += struct.pack(">i", int(erpm))               # rpm (ERPM)
    p += struct.pack(">h", int(v_in * 10))          # v_in
    p += struct.pack(">i", 0)                       # amp_hours
    p += struct.pack(">i", 0)                       # amp_hours_charged
    p += struct.pack(">i", 0)                       # watt_hours
    p += struct.pack(">i", 0)                       # watt_hours_charged
    p += struct.pack(">i", int(tach))               # tachometer
    p += struct.pack(">i", abs(int(tach)))          # tachometer_abs
    p.append(0)                                     # fault_code
    p += struct.pack(">i", 0)                       # pid_pos_now
    p.append(64)                                    # controller_id
    p += struct.pack(">hhh", 300, 300, 300)         # temp_mos1..3
    p += struct.pack(">ii", 0, 0)                   # vd, vq
    return build_vesc_packet(bytes(p))


def build_fake_get_values_selective(
    mask, erpm=0, v_in=27.1, current_motor=0.0, current_in=0.0, duty=0.0, tach=0
):
    """Build a VESC v5.02 COMM_GET_VALUES_SELECTIVE response frame."""
    p = bytearray()
    p.append(50)  # COMM_GET_VALUES_SELECTIVE
    p += struct.pack(">I", mask)
    if mask & (1 << 0):
        p += struct.pack(">h", 300)
    if mask & (1 << 1):
        p += struct.pack(">h", 280)
    if mask & (1 << 2):
        p += struct.pack(">i", int(current_motor * 100))
    if mask & (1 << 3):
        p += struct.pack(">i", int(current_in * 100))
    if mask & (1 << 4):
        p += struct.pack(">i", 0)
    if mask & (1 << 5):
        p += struct.pack(">i", 0)
    if mask & (1 << 6):
        p += struct.pack(">h", int(duty * 1000))
    if mask & (1 << 7):
        p += struct.pack(">i", int(erpm))
    if mask & (1 << 8):
        p += struct.pack(">h", int(v_in * 10))
    if mask & (1 << 9):
        p += struct.pack(">i", 0)
    if mask & (1 << 10):
        p += struct.pack(">i", 0)
    if mask & (1 << 11):
        p += struct.pack(">i", 0)
    if mask & (1 << 12):
        p += struct.pack(">i", 0)
    if mask & (1 << 13):
        p += struct.pack(">i", int(tach))
    if mask & (1 << 14):
        p += struct.pack(">i", abs(int(tach)))
    if mask & (1 << 15):
        p.append(0)
    if mask & (1 << 16):
        p += struct.pack(">i", 0)
    if mask & (1 << 17):
        p.append(64)
    if mask & (1 << 18):
        p += struct.pack(">hhh", 300, 300, 300)
    if mask & (1 << 19):
        p += struct.pack(">i", 0)
    if mask & (1 << 20):
        p += struct.pack(">i", 0)
    return build_vesc_packet(bytes(p))


def decode_payload(payload: bytes) -> str:
    if not payload:
        return "EMPTY"
    cmd = payload[0]
    name = CMD_NAMES.get(cmd, f"CMD_{cmd}")
    rest = payload[1:]
    if cmd == 35 and len(rest) >= 4:  # COMM_SET_CHUCK_DATA
        js_x, js_y, bt_c, bt_z = rest[0], rest[1], rest[2], rest[3]
        extra = ""
        if len(rest) >= 10:
            ax, ay, az = struct.unpack(">hhh", rest[4:10])
            extra = f" acc=({ax},{ay},{az})"
        if len(rest) > 10:
            extra += f" tail={rest[10:].hex()}"
        return f"{name}: js_x={js_x} js_y={js_y} bt_c={bt_c} bt_z={bt_z}{extra}"
    if cmd == 5 and len(rest) >= 4:
        return f"{name}: duty={struct.unpack('>i', rest[:4])[0] / 1e5:.4f}"
    if cmd in (6, 7, 10) and len(rest) >= 4:
        return f"{name}: current={struct.unpack('>i', rest[:4])[0] / 1e3:.3f} A"
    if cmd == 8 and len(rest) >= 4:
        return f"{name}: erpm={struct.unpack('>i', rest[:4])[0]}"
    if cmd == 50 and len(rest) >= 4:
        mask = struct.unpack(">I", rest[:4])[0]
        return f"{name}: mask=0x{mask:08x}"
    if cmd == 34 and len(rest) >= 2:
        can_id = rest[0]
        return f"{name}(id={can_id}) -> {decode_payload(rest[1:])}"
    return f"{name} (len={len(rest)}): {rest.hex(' ')}"


def main():
    ap = argparse.ArgumentParser(
        description="Sniff Flipsky VX1 / AtmosGear Remote AG1 UART packets and optionally emulate a VESC."
    )
    ap.add_argument("--port", default="/dev/serial0", help="Serial device (default: /dev/serial0)")
    ap.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    ap.add_argument("--duration", type=float, default=15.0, help="Capture duration in seconds")
    ap.add_argument("--fake-vesc", action="store_true", help="Reply to telemetry requests as a VESC v5.02")
    ap.add_argument("--erpm", type=int, default=0, help="Simulated ERPM when --fake-vesc is enabled")
    ap.add_argument("--vin", type=float, default=27.1, help="Simulated battery voltage (V)")
    ap.add_argument("--raw", action="store_true", help="Also print raw incoming hex chunks")
    args = ap.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.05)
    ser.reset_input_buffer()
    print(
        f"Listening on {args.port} @ {args.baud} for {args.duration}s "
        f"(fake_vesc={args.fake_vesc}, erpm={args.erpm}, vin={args.vin})",
        flush=True,
    )

    buf = bytearray()
    t0 = time.time()
    last_by_cmd = {}
    counts = {}
    raw_total = 0
    bad_bytes = bytearray()

    while time.time() - t0 < args.duration:
        chunk = ser.read(256)
        if chunk:
            raw_total += len(chunk)
            if args.raw:
                print(f"[{time.time() - t0:6.2f}s] RAW({len(chunk)}): {chunk.hex(' ')}", flush=True)
            buf.extend(chunk)

        while len(buf) >= 6:
            if buf[0] == 2:
                plen = buf[1]
                frame_len = 2 + plen + 3
                hdr_len = 2
            elif buf[0] == 3:
                plen = (buf[1] << 8) | buf[2]
                frame_len = 3 + plen + 3
                hdr_len = 3
            else:
                bad_bytes.append(buf.pop(0))
                continue

            if len(buf) < frame_len:
                break

            if buf[frame_len - 1] != 3:
                bad_bytes.append(buf.pop(0))
                continue

            payload = bytes(buf[hdr_len : hdr_len + plen])
            crc_rx = struct.unpack(">H", buf[hdr_len + plen : hdr_len + plen + 2])[0]
            if crc16_vesc(payload) != crc_rx:
                bad_bytes.append(buf.pop(0))
                continue

            if bad_bytes:
                print(
                    f"[{time.time() - t0:6.2f}s] NON-VESC ({len(bad_bytes)} B): {bad_bytes[:40].hex(' ')}",
                    flush=True,
                )
                bad_bytes.clear()

            del buf[:frame_len]
            cmd = payload[0]
            counts[cmd] = counts.get(cmd, 0) + 1
            decoded = decode_payload(payload)
            if last_by_cmd.get(cmd) != decoded:
                last_by_cmd[cmd] = decoded
                print(f"[{time.time() - t0:6.2f}s] {decoded}", flush=True)

            if args.fake_vesc:
                dt = time.time() - t0
                tach = int(args.erpm * dt / 60.0 * 6)
                if cmd == 4:
                    ser.write(build_fake_get_values(erpm=args.erpm, v_in=args.vin, tach=tach))
                elif cmd == 50 and len(payload) >= 5:
                    mask = struct.unpack(">I", payload[1:5])[0]
                    ser.write(build_fake_get_values_selective(mask, erpm=args.erpm, v_in=args.vin, tach=tach))
                elif cmd == 0:
                    fw = bytes([0, 5, 2]) + b"410\x00" + bytes(12) + bytes([0, 0, 1])
                    ser.write(build_vesc_packet(fw))

    if bad_bytes or buf:
        rem = bytes(bad_bytes) + bytes(buf)
        print(f"REMAINING NON-VESC ({len(rem)} B): {rem[:80].hex(' ')}", flush=True)
    summary = {CMD_NAMES.get(k, f"CMD_{k}"): v for k, v in counts.items()}
    print(f"DONE. total_bytes={raw_total}, packet_counts={summary}", flush=True)


if __name__ == "__main__":
    main()
