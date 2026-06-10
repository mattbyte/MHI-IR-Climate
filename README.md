# MHI IR Climate

![MHI IR Climate logo](custom_components/mhi_ir_climate/brand/logo.png)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)

MHI IR Climate is a Home Assistant custom integration for controlling Mitsubishi Heavy Industries ZSA-series air conditioners, commonly known as the Avanti series, through Home Assistant's native `infrared` platform.

It creates a normal Home Assistant `climate` entity for an IR-only air conditioner and sends complete Mitsubishi Heavy Industries IR state frames through a selected infrared emitter. It is designed to work with native infrared emitters, including entities provided by [IR Wrapper for Zigbee IR Blasters](https://github.com/tomer2526/IR-Wrapper-for-Zigbee-IR-Bluster).

## ✅ What You Need

- Home Assistant 2026.4.0 or newer.
- A native Home Assistant `infrared` emitter entity in the room with the air conditioner.
- For Tuya/Zosung-style Zigbee IR blasters, install and configure [IR Wrapper for Zigbee IR Blasters](https://github.com/tomer2526/IR-Wrapper-for-Zigbee-IR-Bluster) first.
- A supported Mitsubishi Heavy Industries ZSA/Avanti indoor unit or a compatible model using the same 19-byte command frame.

## 🧪 Tested Hardware

This integration was built from decoded IR captures for:

- Mitsubishi Heavy Industries DXK09ZSA-W with remote RLA502A720.
- Mitsubishi Heavy Industries SRK35ZSA-W with remote RLA502A700L.
- Tuya/Zosung-style Zigbee IR blasters exposed to Home Assistant as native infrared emitters.
- Broadlink RM4 Mini IR blaster through the official Home Assistant Broadlink integration.

## 🚀 Installation With HACS

1. In Home Assistant, open **HACS**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add `https://github.com/mattbyte/MHI-IR-Climate`.
4. Select **Integration** as the category.
5. Download **MHI IR Climate**.
6. Restart Home Assistant.
7. Go to **Settings** -> **Devices & services** -> **Add integration** and search for **MHI IR Climate**.

## ⚙️ Configuration

Add one integration entry per air conditioner.

During setup, choose:

- **Name**: The climate entity name, such as `Living AC`.
- **Infrared emitter**: The native `infrared` emitter entity in the same room.
- **Base IR frame**: A 19-byte hexadecimal base frame. Most users should leave the default:

```text
52aec31ae5f609f807ff004db25aa5ff007f80
```

- **Room temperature sensor**: Optional sensor shown as the climate current temperature.
- **Room humidity sensor**: Optional sensor shown as the climate current humidity.

The device model shown in Home Assistant is fixed as **MHI ZSA Series (Avanti)** because the current protocol profile is shared by the tested ZSA/Avanti units.

## 🕹️ Features

- Adds a Home Assistant `climate` entity from the UI.
- Links each climate entity to a selected native `infrared` emitter entity.
- Supports `off`, `cool`, `heat`, `dry`, `fan only`, and `heat/cool` HVAC modes.
- Supports target temperatures from 18 C to 30 C in 1 C steps.
- Supports fan speeds: `Auto`, `Very Low`, `Low`, `Medium`, and `High`.
- Supports `Boost`, `Silent`, and `Night Setback` climate presets. `Night Setback` switches the entity to heat mode before sending the IR command.
- Clears `Boost` in Home Assistant state after 15 minutes without sending another IR command.
- Supports vertical swing modes: `3D Auto`, `Stop`, `0 Deg`, `30 Deg`, `45 Deg`, `60 Deg`, `90 Deg`, and `Moving`.
- Supports horizontal swing modes: `3D Auto`, `Stop`, `Hard Left`, `Left`, `Straight`, `Right`, `Hard Right`, `Wide`, `Narrow`, and `Moving`.
- Keeps `3D Auto` coupled across both swing axes, while restoring the other axis to its last non-3D mode when a normal swing mode is selected.
- Falls back to the last non-3D swing modes, or `Stop` when unknown, when `dry` or `fan only` mode is active because `3D Auto` is not available in those modes.
- Restores the last HVAC mode, target temperature, fan mode, preset, and swing mode after Home Assistant restarts.

## 🧰 Device Controls

The integration also adds configuration entities on the device page:

- **Power LED brightness** select: `Dim`, `Normal`, and `Off`.
- **Installation position** select: `Left`, `Centre`, and `Right`. This command can only be sent while the air conditioner is off.
- **Auto clean** switch, including clean-cycle turn-off commands for cool, dry, and heat/cool modes.
- **Force send IR command** button for resending the current Home Assistant state when the physical unit and Home Assistant are out of sync.

## 📡 How It Works

IR-controlled air conditioners usually expect every command to describe the whole desired state, not just the changed setting. When you change mode, temperature, fan, swing, preset, or a supported device setting, this integration builds a complete MHI frame and sends it as raw infrared timings through Home Assistant's `infrared.async_send_command` helper.

For Zosung/Tuya Zigbee IR blasters, the companion Zigbee IR wrapper receives those raw timings and converts them into the `ir_code_to_send` payload required by Zigbee2MQTT or ZHA.

## ⚠️ Current Limitations

- Only captured ZSA/Avanti command mappings are implemented.
- IR is one-way. The climate entity is optimistic and restores its last known state, but it cannot confirm what the physical air conditioner actually did.

## 🛠️ Development Notes

The protocol builder in `custom_components/mhi_ir_climate/ir_protocol.py` is based on decoded IR captures and the original working pyscript encoder. It keeps the MHI frame manipulation local to this integration and leaves IR transport and Zigbee payload encoding to Home Assistant's native infrared emitter layer.
