# MHI IR Climate

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)

MHI IR Climate is a Home Assistant custom integration for controlling selected Mitsubishi Heavy Industries air conditioners through Home Assistant's native `infrared` platform.

It creates normal `climate` entities for IR-only air conditioners and sends full-state IR commands through an infrared emitter entity, such as one provided by [IR Wrapper for Zigbee IR Blasters](https://github.com/tomer2526/IR-Wrapper-for-Zigbee-IR-Bluster).

## Tested Hardware

This integration was created from working captures and scripts for:

- Mitsubishi Heavy Industries DXK09ZSA-W with remote RLA502A720
- Mitsubishi Heavy Industries SRK35ZSA-W with remote RLA502A700L
- Tuya/Zosung-style Zigbee IR blasters exposed to Home Assistant as native infrared emitters

The default protocol profile is intended for MHI ZSA-series units, commonly known as the Avanti series, that use the same 19-byte command frame structure.

## Features

- Adds a Home Assistant `climate` entity from the UI.
- Links each climate entity to a selected native `infrared` emitter entity.
- Supports `off`, `cool`, `heat`, `dry`, `fan only`, and `heat/cool` HVAC modes.
- Supports target temperatures from 18 C to 30 C in 1 C steps.
- Supports fan speeds: `Auto`, `Very Low`, `Low`, `Medium`, and `High`.
- Adds a device configuration select for power LED brightness: `Dim`, `Normal`, and `Off`.
- Adds a device configuration button to force-send the current IR state when Home Assistant and the physical unit are out of sync.
- Supports vertical swing modes: `3D Auto`, `Stop`, `0 Deg`, `30 Deg`, `45 Deg`, `60 Deg`, `90 Deg`, and `Moving`.
- Supports horizontal swing modes: `3D Auto`, `Stop`, `Hard Left`, `Left`, `Straight`, `Right`, `Hard Right`, `Wide`, `Narrow`, and `Moving`.
- Keeps `3D Auto` coupled across both swing axes, while restoring the other axis to its last non-3D mode when a normal swing mode is selected.
- Falls back to the last non-3D swing modes, or `Stop` when unknown, when `dry` or `fan only` mode is active because `3D Auto` is not available in those modes.
- Restores the last HVAC mode, target temperature, and swing mode after Home Assistant restarts.
- Optionally displays current room temperature and humidity from existing sensor entities.
- Sends raw protocol timings through Home Assistant's infrared abstraction. The Zigbee IR wrapper handles the FastLZ/base64 encoding required by Zosung/Tuya Zigbee blasters.

## Requirements

- Home Assistant 2026.4.0 or newer.
- At least one native Home Assistant `infrared` emitter entity.
- For Zigbee2MQTT or ZHA IR blasters, install and configure [IR Wrapper for Zigbee IR Blasters](https://github.com/tomer2526/IR-Wrapper-for-Zigbee-IR-Bluster) first.

## Installation With HACS

1. Upload this repository to GitHub.
2. In Home Assistant, open HACS.
3. Open the three-dot menu and choose **Custom repositories**.
4. Add your repository URL.
5. Select **Integration** as the category.
6. Download **MHI IR Climate**.
7. Restart Home Assistant.
8. Go to **Settings** -> **Devices & services** -> **Add integration** and search for **MHI IR Climate**.

## Configuration

Add one integration entry per air conditioner.

During setup, choose:

- **Name**: The climate entity name, such as `Living AC`.
- **Infrared emitter**: The native `infrared` emitter entity in the same room.
- **Model**: The closest tested model/profile.
- **Base IR frame**: A 19-byte hexadecimal base frame. The default is:

```text
52aec31ae5f609f807ff004db25aa5ff007f80
```

- **Room temperature sensor**: Optional.
- **Room humidity sensor**: Optional.

## How It Works

IR-controlled air conditioners usually expect each command to describe the whole desired state, not just the changed setting. When you change mode, temperature, or swing, this integration builds a complete MHI frame and sends it as raw infrared timings through Home Assistant's `infrared.async_send_command` helper.

For Zosung/Tuya Zigbee IR blasters, the companion Zigbee IR wrapper receives those raw timings and converts them into the `ir_code_to_send` payload required by Zigbee2MQTT or ZHA.

## Current Limitations

- Only captured ZSA/Avanti command mappings are implemented.
- Fan speed, dry mode, auto mode, and horizontal swing are not exposed yet because the supplied working setup did not include stable frame mappings for those controls.
- IR is one-way. The climate entity is optimistic and restores its last known state, but it cannot confirm what the physical air conditioner actually did.

## Development Notes

The protocol builder in `custom_components/mhi_ir_climate/ir_protocol.py` is based on the working pyscript encoder. It keeps the MHI frame manipulation local to this integration and leaves IR transport/encoding to Home Assistant's native infrared emitter layer.
