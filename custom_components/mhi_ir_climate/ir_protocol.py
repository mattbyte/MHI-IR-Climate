"""Mitsubishi Heavy Industries ZSA-series IR command builder."""

from __future__ import annotations

from typing import Final, Literal

from infrared_protocols.commands import Command

Mode = Literal["cool", "heat"]

DEFAULT_BASE_FRAME_HEX: Final = "52aec31ae5f609f807ff004db25aa5ff007f80"
DEFAULT_CARRIER_FREQUENCY: Final = 38_000

TEMP_NIBBLE_START: Final = 64
TEMP_COMP_START: Final = 56

MODE_BITS: Final = (40, 42, 48, 50)
COOL_PATTERN: Final = (0, 1, 1, 0)
HEAT_PATTERN: Final = (1, 0, 0, 1)

POWER_BITS: Final = (43, 51)

SWING_UD_BYTE: Final = 11
SWING_LR_BYTE: Final = 13

UD_CODES: Final = {
    "3d_auto": 0x2D,
    "3d": 0x2D,
    "stop": 0x3F,
    "0": 0xDF,
    "0deg": 0xDF,
    "0_deg": 0xDF,
    "30": 0xBF,
    "30deg": 0xBF,
    "30_deg": 0xBF,
    "45": 0x9F,
    "45deg": 0x9F,
    "45_deg": 0x9F,
    "60": 0x7F,
    "60deg": 0x7F,
    "60_deg": 0x7F,
    "90": 0x5F,
    "90deg": 0x5F,
    "90_deg": 0x5F,
    "moving": 0xFF,
}

LR_CODES: Final = {
    "stop": 0x37,
    "hard_left": 0x3E,
    "left": 0x3D,
    "straight": 0x3C,
    "stright": 0x3C,
    "right": 0x3B,
    "hard_right": 0x3A,
    "wide": 0x38,
    "narrow": 0x39,
    "moving": 0x3F,
}

SWING_MODES: Final = (
    "3D Auto",
    "Stop",
    "0 Deg",
    "30 Deg",
    "45 Deg",
    "60 Deg",
    "90 Deg",
    "Moving",
)


class MHIIRCommand(Command):
    """Raw IR command for the HA infrared platform."""

    def __init__(
        self,
        timings: list[int],
        *,
        modulation: int = DEFAULT_CARRIER_FREQUENCY,
        repeat_count: int = 0,
    ) -> None:
        """Initialize the command."""

        super().__init__(modulation=modulation, repeat_count=repeat_count)
        self._timings = timings

    def get_raw_timings(self) -> list[int]:
        """Return signed raw timings in microseconds."""

        return list(self._timings)


def build_mhi_ir_command(
    mode: Mode,
    temperature_c: int,
    power_on: bool,
    base_frame_hex: str,
    swing_ud: str | None = None,
    swing_lr: str | None = None,
) -> MHIIRCommand:
    """Build an MHI IR command for Home Assistant's infrared helpers."""

    frame = build_ac_frame_bytes(
        mode,
        temperature_c,
        power_on,
        base_frame_hex=base_frame_hex,
        swing_ud=swing_ud,
        swing_lr=swing_lr,
    )
    pulses = frame_to_pulses_us(frame)
    return MHIIRCommand(_pulses_to_signed_timings(pulses))


def validate_base_frame_hex(base_frame_hex: str) -> None:
    """Validate the configured 19-byte base frame."""

    frame = bytes.fromhex(base_frame_hex)
    if len(frame) != 19:
        raise ValueError("base_frame_hex must decode to 19 bytes")


def build_ac_frame_bytes(
    mode: Mode,
    temperature_c: int,
    power_on: bool,
    base_frame_hex: str,
    swing_ud: str | None = None,
    swing_lr: str | None = None,
) -> bytes:
    """Return the 19-byte MHI AC frame for the requested state."""

    if mode not in ("cool", "heat"):
        raise ValueError("mode must be 'cool' or 'heat'")
    if not 18 <= temperature_c <= 30:
        raise ValueError("temperature_c must be 18..30")

    frame = bytearray(bytes.fromhex(base_frame_hex))
    if len(frame) != 19:
        raise ValueError("base_frame_hex must decode to 19 bytes")

    pattern = COOL_PATTERN if mode == "cool" else HEAT_PATTERN
    for bit_index, bit_value in zip(MODE_BITS, pattern, strict=True):
        _set_bit(frame, bit_index, bit_value)

    temp_code = temperature_c - 17
    comp_code = 15 - temp_code
    _set_nibble_lsb_first(frame, TEMP_NIBBLE_START, temp_code)
    _set_nibble_lsb_first(frame, TEMP_COMP_START, comp_code)

    ud_code, lr_code = _pick_swing_codes(swing_ud, swing_lr)
    frame[SWING_UD_BYTE] = ud_code
    frame[SWING_UD_BYTE + 1] = ud_code ^ 0xFF
    frame[SWING_LR_BYTE] = lr_code
    frame[SWING_LR_BYTE + 1] = lr_code ^ 0xFF

    if not power_on:
        for bit_index in POWER_BITS:
            frame[bit_index // 8] ^= 1 << (bit_index % 8)

    return bytes(frame)


def frame_to_pulses_us(
    frame: bytes,
    header_mark_us: int = 3176,
    header_space_us: int = 1642,
    bit_mark_us: int = 399,
    zero_space_us: int = 399,
    one_space_us: int = 1241,
    trailer_mark_us: int = 344,
) -> list[int]:
    """Convert a frame to alternating positive pulse/space durations."""

    pulses = [header_mark_us, header_space_us]
    for byte in frame:
        for bit_position in range(8):
            bit = (byte >> bit_position) & 1
            pulses.append(bit_mark_us)
            pulses.append(one_space_us if bit else zero_space_us)
    pulses.append(trailer_mark_us)
    return pulses


def _set_bit(buf: bytearray, bit_index: int, value: int) -> None:
    byte_index = bit_index // 8
    bit_position = bit_index % 8
    mask = 1 << bit_position
    if value:
        buf[byte_index] |= mask
    else:
        buf[byte_index] &= ~mask


def _set_nibble_lsb_first(buf: bytearray, start_bit: int, nibble: int) -> None:
    for offset in range(4):
        _set_bit(buf, start_bit + offset, (nibble >> offset) & 1)


def _normalize_swing(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().lower()
    normalized = normalized.replace("\u00b0", "deg").replace("\u00c2", "")
    normalized = normalized.replace("/", "_").replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    normalized = normalized.replace("3dauto", "3d_auto")
    return normalized


def _pick_swing_codes(
    swing_ud: str | None,
    swing_lr: str | None,
) -> tuple[int, int]:
    ud = _normalize_swing(swing_ud)
    lr = _normalize_swing(swing_lr)

    if ud in ("3d_auto", "3d") or lr in ("3d_auto", "3d"):
        return UD_CODES["3d_auto"], LR_CODES["stop"]

    if ud is None and lr is None:
        return UD_CODES["3d_auto"], LR_CODES["stop"]

    if ud is None:
        ud_code = UD_CODES["stop"]
    elif ud in UD_CODES:
        ud_code = UD_CODES[ud]
    else:
        raise ValueError(f"Unknown up/down swing mode: {swing_ud}")

    if lr is None:
        lr_code = LR_CODES["stop"]
    elif lr in LR_CODES:
        lr_code = LR_CODES[lr]
    else:
        raise ValueError(f"Unknown left/right swing mode: {swing_lr}")

    return ud_code, lr_code


def _pulses_to_signed_timings(pulses: list[int]) -> list[int]:
    return [
        int(duration) if index % 2 == 0 else -int(duration)
        for index, duration in enumerate(pulses)
    ]
