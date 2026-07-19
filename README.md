# ESP32 Sensor Dashboard

A MicroPython application for ESP32 that monitors temperature and potentiometer sensors while controlling an RGB LED via a web-based dashboard.

## Features

- **Dual LED Control Modes**: Toggle between potentiometer and temperature-based RGB brightness
- **Temperature Monitoring**: Real-time readings from MCP9808 temperature sensor via I2C
- **Potentiometer Input**: Analog control for manual LED brightness adjustment
- **Digital Pin Monitoring**: Reads status of up to 4 configurable digital input pins
- **Web Dashboard**: HTML interface for viewing sensor data and remote control
- **REST API**: JSON endpoints for programmatic sensor access
- **Asynchronous Operation**: Concurrent execution of sensor monitoring, button control, and web server

## Hardware Requirements

- ESP32 microcontroller
- MCP9808 temperature sensor (I2C interface)
- Potentiometer (connected to ADC pin 34)
- RGB LED with individual PWM control (pins 32, 15, 14)
- Push button (pin 33, active low with pull-up)
- Digital input pins (0, 2, 4, 5)

## Pin Configuration

| Component | Pin(s) | Type |
|-----------|--------|------|
| Temperature Sensor (I2C) | 22 (SCL), 23 (SDA) | I2C |
| Potentiometer | 34 | ADC |
| LED Red | 32 | PWM |
| LED Green | 15 | PWM |
| LED Blue | 14 | PWM |
| Button | 33 | Digital Input |
| Digital Inputs | 0, 2, 4, 5 | Digital Input |

## Installation

1. Flash MicroPython to your ESP32
2. Upload this script to the device
3. The ESP32 will create a WiFi access point named `WiFi`
4. Connect to the access point and navigate to `http://192.168.4.1` in your browser

## Usage

Displays current sensor readings, LED mode, and RGB duty cycle.

### Control Modes

- **Potentiometer Mode (default)**: RGB brightness controlled by potentiometer value
- **Temperature Mode**: RGB brightness scales with temperature (25°C = 0%, 35°C = 100%)

Toggle modes by pressing the button on pin 33 or using the web interface.

## API Endpoints

### GET /

Returns HTML dashboard with sensor data and controls.

### GET /sensors

Returns JSON object with all sensor readings:

```json
{
  "potentiometer": 2048,
  "temperature": 24.5,
  "rgb\_duty": 512,
  "mode": "pot",
  "button": 1
}
```
### GET /pins
```json
{
  "pins": [
    {"pin": 0, "value": 1},
    {"pin": 2, "value": 0},
    {"pin": 4, "value": 1},
    {"pin": 5, "value": 1}
  ]
}
```

### GET /led?mode=pot

Switch to potentiometer control mode.

### GET /led?mode=temp

Switch to temperature control mode.


License

MIT

Author

Created for ESP32 microcontroller projects.
