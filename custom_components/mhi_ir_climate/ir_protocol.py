"""Mitsubishi Heavy Industries ZSA-series IR command builder."""

from __future__ import annotations

from typing import Final, Literal

from infrared_protocols.commands import Command

Mode = Literal["cool", "heat", "dry", "fan_only", "heat_cool"]

DEFAULT_BASE_FRAME_HEX: Final = "52aec31ae5f609f807ff004db25aa5ff007f80"
DEFAULT_CARRIER_FREQUENCY: Final = 38_000

TEMP_NIBBLE_START: Final = 64
TEMP_COMP_START: Final = 56

MODE_BYTE: Final = 5
MODE_COMP_BYTE: Final = 6
MODE_CODES: Final = {
    "cool": 0xF6,
    "heat": 0xF3,
    "dry": 0xF5,
    "fan_only": 0xF4,
    "heat_cool": 0xF7,
}

POWER_BITS: Final = (43, 51)

SWING_UD_BYTE: Final = 11
SWING_LR_BYTE: Final = 13

FAN_BYTE: Final = 9
FAN_COMP_BYTE: Final = 10

FAN_AUTO = "Auto"
FAN_VERY_LOW = "Very Low"
FAN_LOW = "Low"
FAN_MEDIUM = "Medium"
FAN_HIGH = "High"
FAN_MODES: Final = (
    FAN_AUTO,
    FAN_VERY_LOW,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)
DEFAULT_FAN_MODE: Final = FAN_AUTO
FAN_CODES: Final = {
    "auto": 0xFF,
    "very_low": 0xFE,
    "low": 0xFD,
    "medium": 0xFC,
    "med": 0xFC,
    "high": 0xFB,
}

PRESET_NONE = "none"
PRESET_BOOST = "boost"
PRESET_SILENT = "Silent"
PRESET_MODES: Final = (
    PRESET_NONE,
    PRESET_BOOST,
    PRESET_SILENT,
)
DEFAULT_PRESET_MODE: Final = PRESET_NONE
PRESET_KEYS: Final = {
    "none": PRESET_NONE,
    "boost": PRESET_BOOST,
    "powerful": PRESET_BOOST,
    "silent": PRESET_SILENT,
}
PRESET_BYTE: Final = 15
PRESET_COMP_BYTE: Final = 16
SILENT_PRESET_CODE: Final = 0x7F
NORMAL_PRESET_CODE: Final = 0xFF
BOOST_FAN_MASK: Final = 0x08

LED_BRIGHTNESS_DIM = "Dim"
LED_BRIGHTNESS_NORMAL = "Normal"
LED_BRIGHTNESS_OFF = "Off"
LED_BRIGHTNESS_MODES: Final = (
    LED_BRIGHTNESS_DIM,
    LED_BRIGHTNESS_NORMAL,
    LED_BRIGHTNESS_OFF,
)
DEFAULT_LED_BRIGHTNESS: Final = LED_BRIGHTNESS_NORMAL
LED_BRIGHTNESS_KEYS: Final = {
    "dim": LED_BRIGHTNESS_DIM,
    "normal": LED_BRIGHTNESS_NORMAL,
    "off": LED_BRIGHTNESS_OFF,
}
LED_DIM_LR_MASK: Final = 0x10
LED_OFF_BYTE: Final = 17
LED_OFF_MASK: Final = 0x01

DEFAULT_AUTO_CLEAN: Final = False
AUTO_CLEAN_MASK: Final = 0x04
AUTO_CLEAN_START_MODES: Final = ("cool", "dry", "heat_cool")
AUTO_CLEAN_START_MODE_NIBBLE: Final = 0x90

INSTALL_POSITION_LEFT = "Left"
INSTALL_POSITION_CENTRE = "Centre"
INSTALL_POSITION_RIGHT = "Right"
INSTALL_POSITION_MODES: Final = (
    INSTALL_POSITION_LEFT,
    INSTALL_POSITION_CENTRE,
    INSTALL_POSITION_RIGHT,
)
DEFAULT_INSTALL_POSITION: Final = INSTALL_POSITION_CENTRE
INSTALL_POSITION_KEYS: Final = {
    "left": INSTALL_POSITION_LEFT,
    "left_side": INSTALL_POSITION_LEFT,
    "centre": INSTALL_POSITION_CENTRE,
    "center": INSTALL_POSITION_CENTRE,
    "right": INSTALL_POSITION_RIGHT,
    "right_side": INSTALL_POSITION_RIGHT,
}
INSTALL_POSITION_MASK: Final = 0x60
INSTALL_POSITION_CODES: Final = {
    INSTALL_POSITION_LEFT: 0x00,
    INSTALL_POSITION_RIGHT: 0x20,
    INSTALL_POSITION_CENTRE: 0x40,
}

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

SWING_HORIZONTAL_MODES: Final = (
    "3D Auto",
    "Stop",
    "Hard Left",
    "Left",
    "Straight",
    "Right",
    "Hard Right",
    "Wide",
    "Narrow",
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
    auto_clean: bool = DEFAULT_AUTO_CLEAN,
    fan_mode: str = DEFAULT_FAN_MODE,
    led_brightness: str = DEFAULT_LED_BRIGHTNESS,
    preset_mode: str = DEFAULT_PRESET_MODE,
    start_auto_clean: bool = False,
    install_position: str | None = None,
    swing_ud: str | None = None,
    swing_lr: str | None = None,
) -> MHIIRCommand:
    """Build an MHI IR command for Home Assistant's infrared helpers."""

    frame = build_ac_frame_bytes(
        mode,
        temperature_c,
        power_on,
        base_frame_hex=base_frame_hex,
        auto_clean=auto_clean,
        fan_mode=fan_mode,
        led_brightness=led_brightness,
        preset_mode=preset_mode,
        start_auto_clean=start_auto_clean,
        install_position=install_position,
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
    auto_clean: bool = DEFAULT_AUTO_CLEAN,
    fan_mode: str = DEFAULT_FAN_MODE,
    led_brightness: str = DEFAULT_LED_BRIGHTNESS,
    preset_mode: str = DEFAULT_PRESET_MODE,
    start_auto_clean: bool = False,
    install_position: str | None = None,
    swing_ud: str | None = None,
    swing_lr: str | None = None,
) -> bytes:
    """Return the 19-byte MHI AC frame for the requested state."""

    if mode not in MODE_CODES:
        raise ValueError(f"mode must be one of {sorted(MODE_CODES)}")
    if not 18 <= temperature_c <= 30:
        raise ValueError("temperature_c must be 18..30")

    frame = bytearray(bytes.fromhex(base_frame_hex))
    if len(frame) != 19:
        raise ValueError("base_frame_hex must decode to 19 bytes")

    if start_auto_clean:
        if mode not in AUTO_CLEAN_START_MODES:
            raise ValueError(
                "auto clean start can only be sent for cool, dry, or heat_cool"
            )
        power_on = True

    mode_code = MODE_CODES[mode]
    if start_auto_clean:
        mode_code = (mode_code & 0x0F) | AUTO_CLEAN_START_MODE_NIBBLE
    frame[MODE_BYTE] = mode_code
    frame[MODE_COMP_BYTE] = mode_code ^ 0xFF

    temp_code = temperature_c - 17
    comp_code = 15 - temp_code
    _set_nibble_lsb_first(frame, TEMP_NIBBLE_START, temp_code)
    _set_nibble_lsb_first(frame, TEMP_COMP_START, comp_code)

    fan_code = _pick_fan_code(fan_mode)
    frame[FAN_BYTE] = fan_code
    frame[FAN_COMP_BYTE] = fan_code ^ 0xFF

    preset_mode = _pick_preset_mode(preset_mode)
    if preset_mode == PRESET_BOOST:
        frame[FAN_BYTE] = fan_code & ~BOOST_FAN_MASK
        frame[FAN_COMP_BYTE] = frame[FAN_BYTE] ^ 0xFF

    preset_code = (
        SILENT_PRESET_CODE if preset_mode == PRESET_SILENT else NORMAL_PRESET_CODE
    )
    frame[PRESET_BYTE] = preset_code
    frame[PRESET_COMP_BYTE] = preset_code ^ 0xFF

    led_brightness = _pick_led_brightness(led_brightness)
    ud_code, lr_code = _pick_swing_codes(swing_ud, swing_lr)
    lr_code = _apply_led_brightness_to_lr_code(lr_code, led_brightness)
    frame[SWING_UD_BYTE] = ud_code
    frame[SWING_UD_BYTE + 1] = ud_code ^ 0xFF
    frame[SWING_LR_BYTE] = lr_code
    frame[SWING_LR_BYTE + 1] = lr_code ^ 0xFF

    if led_brightness == LED_BRIGHTNESS_OFF:
        frame[LED_OFF_BYTE] &= ~LED_OFF_MASK
    else:
        frame[LED_OFF_BYTE] |= LED_OFF_MASK
    if auto_clean:
        frame[LED_OFF_BYTE] &= ~AUTO_CLEAN_MASK
    else:
        frame[LED_OFF_BYTE] |= AUTO_CLEAN_MASK
    if install_position is not None:
        position = normalize_install_position(install_position)
        frame[LED_OFF_BYTE] = (
            frame[LED_OFF_BYTE] & ~INSTALL_POSITION_MASK
        ) | INSTALL_POSITION_CODES[position]
    frame[LED_OFF_BYTE + 1] = frame[LED_OFF_BYTE] ^ 0xFF

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


def _normalize_fan_mode(value: str) -> str:
    normalized = str(value).strip().lower()
    normalized = normalized.replace("/", "_").replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _pick_fan_code(fan_mode: str) -> int:
    normalized = _normalize_fan_mode(fan_mode)
    if normalized not in FAN_CODES:
        raise ValueError(f"Unknown fan mode: {fan_mode}")
    return FAN_CODES[normalized]


def _pick_preset_mode(preset_mode: str) -> str:
    return normalize_preset_mode(preset_mode)


def normalize_preset_mode(preset_mode: str) -> str:
    normalized = str(preset_mode).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in PRESET_KEYS:
        raise ValueError(f"Unknown preset mode: {preset_mode}")
    return PRESET_KEYS[normalized]


def normalize_install_position(install_position: str) -> str:
    normalized = (
        str(install_position).strip().lower().replace("-", "_").replace(" ", "_")
    )
    if normalized not in INSTALL_POSITION_KEYS:
        raise ValueError(f"Unknown installation position: {install_position}")
    return INSTALL_POSITION_KEYS[normalized]


def _pick_led_brightness(led_brightness: str) -> str:
    normalized = str(led_brightness).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in LED_BRIGHTNESS_KEYS:
        raise ValueError(f"Unknown LED brightness: {led_brightness}")
    return LED_BRIGHTNESS_KEYS[normalized]


def _apply_led_brightness_to_lr_code(lr_code: int, led_brightness: str) -> int:
    if led_brightness == LED_BRIGHTNESS_DIM:
        return lr_code & ~LED_DIM_LR_MASK

    return lr_code | LED_DIM_LR_MASK


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
