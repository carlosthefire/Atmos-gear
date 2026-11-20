#!/usr/bin/env python3
"""
Standalone VESC v5.02 MCCONF / APPCONF binary decoder and differ.

Decodes raw VESC v5.02 payloads captured via COMM_GET_MCCONF (14),
COMM_GET_MCCONF_DEFAULT (15), COMM_GET_APPCONF (17), or
COMM_GET_APPCONF_DEFAULT (18).

Signatures (VESC Firmware 5.02):
  - MCCONF_SIGNATURE  = 2211848314 (0x83d6207a)
  - APPCONF_SIGNATURE = 3264926020 (0xc29ad144)

No external dependencies required (Python 3 standard library only).
"""

import argparse
import json
import math
import struct
import sys
from pathlib import Path

MCCONF_SIGNATURE = 0x83D6207A
APPCONF_SIGNATURE = 0xC29AD144

MCCONF_FIELDS = [('pwm_mode', 'u8', None),
 ('comm_mode', 'u8', None),
 ('motor_type', 'u8', None),
 ('sensor_mode', 'u8', None),
 ('l_current_max', 'f32auto', None),
 ('l_current_min', 'f32auto', None),
 ('l_in_current_max', 'f32auto', None),
 ('l_in_current_min', 'f32auto', None),
 ('l_abs_current_max', 'f32auto', None),
 ('l_min_erpm', 'f32auto', None),
 ('l_max_erpm', 'f32auto', None),
 ('l_erpm_start', 'f32auto', None),
 ('l_max_erpm_fbrake', 'f32auto', None),
 ('l_max_erpm_fbrake_cc', 'f32auto', None),
 ('l_min_vin', 'f32auto', None),
 ('l_max_vin', 'f32auto', None),
 ('l_battery_cut_start', 'f32auto', None),
 ('l_battery_cut_end', 'f32auto', None),
 ('l_slow_abs_current', 'u8', None),
 ('l_temp_fet_start', 'f32auto', None),
 ('l_temp_fet_end', 'f32auto', None),
 ('l_temp_motor_start', 'f32auto', None),
 ('l_temp_motor_end', 'f32auto', None),
 ('l_temp_accel_dec', 'f32auto', None),
 ('l_min_duty', 'f32auto', None),
 ('l_max_duty', 'f32auto', None),
 ('l_watt_max', 'f32auto', None),
 ('l_watt_min', 'f32auto', None),
 ('l_current_max_scale', 'f32auto', None),
 ('l_current_min_scale', 'f32auto', None),
 ('l_duty_start', 'f32auto', None),
 ('sl_min_erpm', 'f32auto', None),
 ('sl_min_erpm_cycle_int_limit', 'f32auto', None),
 ('sl_max_fullbreak_current_dir_change', 'f32auto', None),
 ('sl_cycle_int_limit', 'f32auto', None),
 ('sl_phase_advance_at_br', 'f32auto', None),
 ('sl_cycle_int_rpm_br', 'f32auto', None),
 ('sl_bemf_coupling_k', 'f32auto', None),
 ('hall_table[0]', 'i8', None),
 ('hall_table[1]', 'i8', None),
 ('hall_table[2]', 'i8', None),
 ('hall_table[3]', 'i8', None),
 ('hall_table[4]', 'i8', None),
 ('hall_table[5]', 'i8', None),
 ('hall_table[6]', 'i8', None),
 ('hall_table[7]', 'i8', None),
 ('hall_sl_erpm', 'f32auto', None),
 ('foc_current_kp', 'f32auto', None),
 ('foc_current_ki', 'f32auto', None),
 ('foc_f_sw', 'f32auto', None),
 ('foc_dt_us', 'f32auto', None),
 ('foc_encoder_inverted', 'u8', None),
 ('foc_encoder_offset', 'f32auto', None),
 ('foc_encoder_ratio', 'f32auto', None),
 ('foc_encoder_sin_gain', 'f32auto', None),
 ('foc_encoder_cos_gain', 'f32auto', None),
 ('foc_encoder_sin_offset', 'f32auto', None),
 ('foc_encoder_cos_offset', 'f32auto', None),
 ('foc_encoder_sincos_filter_constant', 'f32auto', None),
 ('foc_sensor_mode', 'u8', None),
 ('foc_pll_kp', 'f32auto', None),
 ('foc_pll_ki', 'f32auto', None),
 ('foc_motor_l', 'f32auto', None),
 ('foc_motor_ld_lq_diff', 'f32auto', None),
 ('foc_motor_r', 'f32auto', None),
 ('foc_motor_flux_linkage', 'f32auto', None),
 ('foc_observer_gain', 'f32auto', None),
 ('foc_observer_gain_slow', 'f32auto', None),
 ('foc_duty_dowmramp_kp', 'f32auto', None),
 ('foc_duty_dowmramp_ki', 'f32auto', None),
 ('foc_openloop_rpm', 'f32auto', None),
 ('foc_openloop_rpm_low', 'f16', 1000.0),
 ('foc_d_gain_scale_start', 'f32auto', None),
 ('foc_d_gain_scale_max_mod', 'f32auto', None),
 ('foc_sl_openloop_hyst', 'f16', 100.0),
 ('foc_sl_openloop_time_lock', 'f16', 100.0),
 ('foc_sl_openloop_time_ramp', 'f16', 100.0),
 ('foc_sl_openloop_time', 'f16', 100.0),
 ('foc_hall_table[0]', 'u8', None),
 ('foc_hall_table[1]', 'u8', None),
 ('foc_hall_table[2]', 'u8', None),
 ('foc_hall_table[3]', 'u8', None),
 ('foc_hall_table[4]', 'u8', None),
 ('foc_hall_table[5]', 'u8', None),
 ('foc_hall_table[6]', 'u8', None),
 ('foc_hall_table[7]', 'u8', None),
 ('foc_hall_interp_erpm', 'f32auto', None),
 ('foc_sl_erpm', 'f32auto', None),
 ('foc_sample_v0_v7', 'u8', None),
 ('foc_sample_high_current', 'u8', None),
 ('foc_sat_comp', 'f16', 1000.0),
 ('foc_temp_comp', 'u8', None),
 ('foc_temp_comp_base_temp', 'f16', 100.0),
 ('foc_current_filter_const', 'f32auto', None),
 ('foc_cc_decoupling', 'u8', None),
 ('foc_observer_type', 'u8', None),
 ('foc_hfi_voltage_start', 'f32auto', None),
 ('foc_hfi_voltage_run', 'f32auto', None),
 ('foc_hfi_voltage_max', 'f32auto', None),
 ('foc_sl_erpm_hfi', 'f32auto', None),
 ('foc_hfi_start_samples', 'u16', None),
 ('foc_hfi_obs_ovr_sec', 'f32auto', None),
 ('foc_hfi_samples', 'u8', None),
 ('gpd_buffer_notify_left', 'i16', None),
 ('gpd_buffer_interpol', 'i16', None),
 ('gpd_current_filter_const', 'f32auto', None),
 ('gpd_current_kp', 'f32auto', None),
 ('gpd_current_ki', 'f32auto', None),
 ('s_pid_kp', 'f32auto', None),
 ('s_pid_ki', 'f32auto', None),
 ('s_pid_kd', 'f32auto', None),
 ('s_pid_kd_filter', 'f32auto', None),
 ('s_pid_min_erpm', 'f32auto', None),
 ('s_pid_allow_braking', 'u8', None),
 ('s_pid_ramp_erpms_s', 'f32auto', None),
 ('p_pid_kp', 'f32auto', None),
 ('p_pid_ki', 'f32auto', None),
 ('p_pid_kd', 'f32auto', None),
 ('p_pid_kd_filter', 'f32auto', None),
 ('p_pid_ang_div', 'f32auto', None),
 ('cc_startup_boost_duty', 'f32auto', None),
 ('cc_min_current', 'f32auto', None),
 ('cc_gain', 'f32auto', None),
 ('cc_ramp_step_max', 'f32auto', None),
 ('m_fault_stop_time_ms', 'i32', None),
 ('m_duty_ramp_step', 'f32auto', None),
 ('m_current_backoff_gain', 'f32auto', None),
 ('m_encoder_counts', 'u32', None),
 ('m_sensor_port_mode', 'u8', None),
 ('m_invert_direction', 'u8', None),
 ('m_drv8301_oc_mode', 'u8', None),
 ('m_drv8301_oc_adj', 'u8', None),
 ('m_bldc_f_sw_min', 'f32auto', None),
 ('m_bldc_f_sw_max', 'f32auto', None),
 ('m_dc_f_sw', 'f32auto', None),
 ('m_ntc_motor_beta', 'f32auto', None),
 ('m_out_aux_mode', 'u8', None),
 ('m_motor_temp_sens_type', 'u8', None),
 ('m_ptc_motor_coeff', 'f32auto', None),
 ('m_hall_extra_samples', 'u8', None),
 ('si_motor_poles', 'u8', None),
 ('si_gear_ratio', 'f32auto', None),
 ('si_wheel_diameter', 'f32auto', None),
 ('si_battery_type', 'u8', None),
 ('si_battery_cells', 'u8', None),
 ('si_battery_ah', 'f32auto', None),
 ('bms.type', 'u8', None),
 ('bms.t_limit_start', 'f16', 100.0),
 ('bms.t_limit_end', 'f16', 100.0),
 ('bms.soc_limit_start', 'f16', 1000.0),
 ('bms.soc_limit_end', 'f16', 1000.0)]

APPCONF_FIELDS = [('controller_id', 'u8', None),
 ('timeout_msec', 'u32', None),
 ('timeout_brake_current', 'f32auto', None),
 ('send_can_status', 'u8', None),
 ('send_can_status_rate_hz', 'u16', None),
 ('can_baud_rate', 'u8', None),
 ('pairing_done', 'u8', None),
 ('permanent_uart_enabled', 'u8', None),
 ('shutdown_mode', 'u8', None),
 ('can_mode', 'u8', None),
 ('uavcan_esc_index', 'u8', None),
 ('uavcan_raw_mode', 'u8', None),
 ('app_to_use', 'u8', None),
 ('app_ppm_conf.ctrl_type', 'u8', None),
 ('app_ppm_conf.pid_max_erpm', 'f32auto', None),
 ('app_ppm_conf.hyst', 'f32auto', None),
 ('app_ppm_conf.pulse_start', 'f32auto', None),
 ('app_ppm_conf.pulse_end', 'f32auto', None),
 ('app_ppm_conf.pulse_center', 'f32auto', None),
 ('app_ppm_conf.median_filter', 'u8', None),
 ('app_ppm_conf.safe_start', 'u8', None),
 ('app_ppm_conf.throttle_exp', 'f32auto', None),
 ('app_ppm_conf.throttle_exp_brake', 'f32auto', None),
 ('app_ppm_conf.throttle_exp_mode', 'u8', None),
 ('app_ppm_conf.ramp_time_pos', 'f32auto', None),
 ('app_ppm_conf.ramp_time_neg', 'f32auto', None),
 ('app_ppm_conf.multi_esc', 'u8', None),
 ('app_ppm_conf.tc', 'u8', None),
 ('app_ppm_conf.tc_max_diff', 'f32auto', None),
 ('app_ppm_conf.max_erpm_for_dir', 'f32auto', None),
 ('app_ppm_conf.smart_rev_max_duty', 'f32auto', None),
 ('app_ppm_conf.smart_rev_ramp_time', 'f32auto', None),
 ('app_adc_conf.ctrl_type', 'u8', None),
 ('app_adc_conf.hyst', 'f32auto', None),
 ('app_adc_conf.voltage_start', 'f32auto', None),
 ('app_adc_conf.voltage_end', 'f32auto', None),
 ('app_adc_conf.voltage_center', 'f32auto', None),
 ('app_adc_conf.voltage2_start', 'f32auto', None),
 ('app_adc_conf.voltage2_end', 'f32auto', None),
 ('app_adc_conf.use_filter', 'u8', None),
 ('app_adc_conf.safe_start', 'u8', None),
 ('app_adc_conf.cc_button_inverted', 'u8', None),
 ('app_adc_conf.rev_button_inverted', 'u8', None),
 ('app_adc_conf.voltage_inverted', 'u8', None),
 ('app_adc_conf.voltage2_inverted', 'u8', None),
 ('app_adc_conf.throttle_exp', 'f32auto', None),
 ('app_adc_conf.throttle_exp_brake', 'f32auto', None),
 ('app_adc_conf.throttle_exp_mode', 'u8', None),
 ('app_adc_conf.ramp_time_pos', 'f32auto', None),
 ('app_adc_conf.ramp_time_neg', 'f32auto', None),
 ('app_adc_conf.multi_esc', 'u8', None),
 ('app_adc_conf.tc', 'u8', None),
 ('app_adc_conf.tc_max_diff', 'f32auto', None),
 ('app_adc_conf.update_rate_hz', 'u16', None),
 ('app_uart_baudrate', 'u32', None),
 ('app_chuk_conf.ctrl_type', 'u8', None),
 ('app_chuk_conf.hyst', 'f32auto', None),
 ('app_chuk_conf.ramp_time_pos', 'f32auto', None),
 ('app_chuk_conf.ramp_time_neg', 'f32auto', None),
 ('app_chuk_conf.stick_erpm_per_s_in_cc', 'f32auto', None),
 ('app_chuk_conf.throttle_exp', 'f32auto', None),
 ('app_chuk_conf.throttle_exp_brake', 'f32auto', None),
 ('app_chuk_conf.throttle_exp_mode', 'u8', None),
 ('app_chuk_conf.multi_esc', 'u8', None),
 ('app_chuk_conf.tc', 'u8', None),
 ('app_chuk_conf.tc_max_diff', 'f32auto', None),
 ('app_chuk_conf.use_smart_rev', 'u8', None),
 ('app_chuk_conf.smart_rev_max_duty', 'f32auto', None),
 ('app_chuk_conf.smart_rev_ramp_time', 'f32auto', None),
 ('app_nrf_conf.speed', 'u8', None),
 ('app_nrf_conf.power', 'u8', None),
 ('app_nrf_conf.crc_type', 'u8', None),
 ('app_nrf_conf.retry_delay', 'u8', None),
 ('app_nrf_conf.retries', 'i8', None),
 ('app_nrf_conf.channel', 'i8', None),
 ('app_nrf_conf.address[0]', 'u8', None),
 ('app_nrf_conf.address[1]', 'u8', None),
 ('app_nrf_conf.address[2]', 'u8', None),
 ('app_nrf_conf.send_crc_ack', 'u8', None),
 ('app_balance_conf.kp', 'f32auto', None),
 ('app_balance_conf.ki', 'f32auto', None),
 ('app_balance_conf.kd', 'f32auto', None),
 ('app_balance_conf.hertz', 'u16', None),
 ('app_balance_conf.fault_pitch', 'f32auto', None),
 ('app_balance_conf.fault_roll', 'f32auto', None),
 ('app_balance_conf.fault_duty', 'f32auto', None),
 ('app_balance_conf.fault_adc1', 'f32auto', None),
 ('app_balance_conf.fault_adc2', 'f32auto', None),
 ('app_balance_conf.fault_delay_pitch', 'u16', None),
 ('app_balance_conf.fault_delay_roll', 'u16', None),
 ('app_balance_conf.fault_delay_duty', 'u16', None),
 ('app_balance_conf.fault_delay_switch_half', 'u16', None),
 ('app_balance_conf.fault_delay_switch_full', 'u16', None),
 ('app_balance_conf.fault_adc_half_erpm', 'u16', None),
 ('app_balance_conf.tiltback_angle', 'f32auto', None),
 ('app_balance_conf.tiltback_speed', 'f32auto', None),
 ('app_balance_conf.tiltback_duty', 'f32auto', None),
 ('app_balance_conf.tiltback_high_voltage', 'f32auto', None),
 ('app_balance_conf.tiltback_low_voltage', 'f32auto', None),
 ('app_balance_conf.tiltback_constant', 'f32auto', None),
 ('app_balance_conf.tiltback_constant_erpm', 'u16', None),
 ('app_balance_conf.startup_pitch_tolerance', 'f32auto', None),
 ('app_balance_conf.startup_roll_tolerance', 'f32auto', None),
 ('app_balance_conf.startup_speed', 'f32auto', None),
 ('app_balance_conf.deadzone', 'f32auto', None),
 ('app_balance_conf.current_boost', 'f32auto', None),
 ('app_balance_conf.multi_esc', 'u8', None),
 ('app_balance_conf.yaw_kp', 'f32auto', None),
 ('app_balance_conf.yaw_ki', 'f32auto', None),
 ('app_balance_conf.yaw_kd', 'f32auto', None),
 ('app_balance_conf.roll_steer_kp', 'f32auto', None),
 ('app_balance_conf.roll_steer_erpm_kp', 'f32auto', None),
 ('app_balance_conf.brake_current', 'f32auto', None),
 ('app_balance_conf.yaw_current_clamp', 'f32auto', None),
 ('app_balance_conf.setpoint_pitch_filter', 'f32auto', None),
 ('app_balance_conf.setpoint_target_filter', 'f32auto', None),
 ('app_balance_conf.setpoint_filter_clamp', 'f32auto', None),
 ('app_balance_conf.kd_pt1_frequency', 'u16', None),
 ('app_pas_conf.ctrl_type', 'u8', None),
 ('app_pas_conf.sensor_type', 'u8', None),
 ('app_pas_conf.current_scaling', 'f16', 1000.0),
 ('app_pas_conf.pedal_rpm_start', 'f16', 10.0),
 ('app_pas_conf.pedal_rpm_end', 'f16', 10.0),
 ('app_pas_conf.invert_pedal_direction', 'u8', None),
 ('app_pas_conf.magnets', 'u16', None),
 ('app_pas_conf.use_filter', 'u8', None),
 ('app_pas_conf.ramp_time_pos', 'f16', 100.0),
 ('app_pas_conf.ramp_time_neg', 'f16', 100.0),
 ('app_pas_conf.update_rate_hz', 'u16', None),
 ('imu_conf.type', 'u8', None),
 ('imu_conf.mode', 'u8', None),
 ('imu_conf.sample_rate_hz', 'u16', None),
 ('imu_conf.accel_confidence_decay', 'f32auto', None),
 ('imu_conf.mahony_kp', 'f32auto', None),
 ('imu_conf.mahony_ki', 'f32auto', None),
 ('imu_conf.madgwick_beta', 'f32auto', None),
 ('imu_conf.rot_roll', 'f32auto', None),
 ('imu_conf.rot_pitch', 'f32auto', None),
 ('imu_conf.rot_yaw', 'f32auto', None),
 ('imu_conf.accel_offsets[0]', 'f32auto', None),
 ('imu_conf.accel_offsets[1]', 'f32auto', None),
 ('imu_conf.accel_offsets[2]', 'f32auto', None),
 ('imu_conf.gyro_offsets[0]', 'f32auto', None),
 ('imu_conf.gyro_offsets[1]', 'f32auto', None),
 ('imu_conf.gyro_offsets[2]', 'f32auto', None),
 ('imu_conf.gyro_offset_comp_fact[0]', 'f32auto', None),
 ('imu_conf.gyro_offset_comp_fact[1]', 'f32auto', None),
 ('imu_conf.gyro_offset_comp_fact[2]', 'f32auto', None),
 ('imu_conf.gyro_offset_comp_clamp', 'f32auto', None)]


def _unpack_float32_auto(buf: bytes, ind: int):
    res = struct.unpack(">I", buf[ind : ind + 4])[0]
    ind += 4
    e = (res >> 23) & 0xFF
    sig_i = res & 0x7FFFFF
    neg = bool(res & (1 << 31))
    sig = 0.0
    if e != 0 or sig_i != 0:
        sig = sig_i / (8388608.0 * 2.0) + 0.5
        e -= 126
    if neg:
        sig = -sig
    return round(math.ldexp(sig, e), 8), ind


def decode_vesc_bin(raw: bytes):
    """Auto-detect MCCONF or APPCONF by 4-byte signature and decode all fields."""
    if len(raw) < 5:
        raise ValueError(f"File too short ({len(raw)} bytes)")

    # Support files with or without the leading 1-byte COMM command ID
    sig_with_cmd = struct.unpack(">I", raw[1:5])[0]
    sig_no_cmd = struct.unpack(">I", raw[0:4])[0]

    if sig_with_cmd in (MCCONF_SIGNATURE, APPCONF_SIGNATURE):
        cmd_id = raw[0]
        sig = sig_with_cmd
        ind = 5
    elif sig_no_cmd in (MCCONF_SIGNATURE, APPCONF_SIGNATURE):
        cmd_id = None
        sig = sig_no_cmd
        ind = 4
    else:
        raise ValueError(
            f"Unknown VESC signature (got 0x{sig_with_cmd:08x} / 0x{sig_no_cmd:08x}). "
            f"Expected VESC v5.02 MCCONF (0x{MCCONF_SIGNATURE:08x}) or APPCONF (0x{APPCONF_SIGNATURE:08x})."
        )

    if sig == MCCONF_SIGNATURE:
        kind = "mcconf"
        fields = MCCONF_FIELDS
    else:
        kind = "appconf"
        fields = APPCONF_FIELDS

    values = {}
    for name, typ, scale in fields:
        if typ == "f32auto":
            val, ind = _unpack_float32_auto(raw, ind)
        elif typ == "f16":
            val = round(struct.unpack(">h", raw[ind : ind + 2])[0] / scale, 6)
            ind += 2
        elif typ == "f32":
            val = round(struct.unpack(">i", raw[ind : ind + 4])[0] / scale, 6)
            ind += 4
        elif typ == "i32":
            val = struct.unpack(">i", raw[ind : ind + 4])[0]
            ind += 4
        elif typ == "u32":
            val = struct.unpack(">I", raw[ind : ind + 4])[0]
            ind += 4
        elif typ == "i16":
            val = struct.unpack(">h", raw[ind : ind + 2])[0]
            ind += 2
        elif typ == "u16":
            val = struct.unpack(">H", raw[ind : ind + 2])[0]
            ind += 2
        elif typ == "i8":
            val = struct.unpack(">b", raw[ind : ind + 1])[0]
            ind += 1
        elif typ == "u8":
            val = raw[ind]
            ind += 1
        else:
            raise ValueError(f"Unsupported type: {typ}")
        values[name] = val

    if ind != len(raw):
        raise ValueError(f"Length mismatch for {kind}: parsed {ind} bytes, file has {len(raw)} bytes")

    return {
        "kind": kind,
        "cmd_id": cmd_id,
        "signature": f"0x{sig:08x}",
        "bytes": len(raw),
        "values": values,
    }


def main():
    ap = argparse.ArgumentParser(description="Decode and diff VESC v5.02 MCCONF/APPCONF binary backups.")
    ap.add_argument("files", nargs="+", type=Path, help="One .bin file to dump, or two .bin files to diff")
    ap.add_argument("--json", action="store_true", help="Output decoded result as JSON")
    args = ap.parse_args()

    decoded = [decode_vesc_bin(p.read_bytes()) for p in args.files]

    if len(decoded) == 1:
        if args.json:
            print(json.dumps(decoded[0], indent=2))
        else:
            d = decoded[0]
            print(f"# {args.files[0].name} ({d['kind']}, sig={d['signature']}, {d['bytes']} bytes)")
            for k, v in d["values"].items():
                print(f"  {k:42s} = {v}")
    elif len(decoded) == 2:
        a, b = decoded
        if a["kind"] != b["kind"]:
            sys.exit(f"Cannot diff {a['kind']} against {b['kind']}")
        diffs = {
            k: {"a": a["values"][k], "b": b["values"][k]}
            for k in a["values"]
            if a["values"][k] != b["values"][k]
        }
        if args.json:
            print(json.dumps(diffs, indent=2))
        else:
            print(f"# DIFF ({a['kind']}): {args.files[0].name}  -->  {args.files[1].name} ({len(diffs)} fields differ)")
            for k, pair in diffs.items():
                print(f"  {k:42s}: {pair['a']!r}  -->  {pair['b']!r}")
    else:
        if args.json:
            out = {p.name: d for p, d in zip(args.files, decoded)}
            print(json.dumps(out, indent=2))
        else:
            sys.exit("Pass 1 file to decode, 2 files to diff, or multiple files with --json.")


if __name__ == "__main__":
    main()
