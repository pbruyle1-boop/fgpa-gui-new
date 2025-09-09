# FPGA GPIO Controller

A web-based FPGA LED controller system using Raspberry Pi GPIO pins, MQTT communication, and modern `pinctrl` commands. Controls 12 individual LEDs (4 per FPGA) with separate pins for each user and loaded status. Compatible with UDN2981A source drivers.

## Features

- **12 Individual GPIO Controls**: 4 LEDs per FPGA (Dan, Nate, Ben, Loaded)
- **Web Interface**: Auto-connecting HTML/JavaScript GUI
- **MQTT Communication**: Real-time bidirectional control
- **Modern GPIO Control**: Uses `pinctrl` commands for Raspberry Pi 4/5
- **UDN2981A Compatible**: Inverted logic support for source drivers
- **Auto-Discovery**: Web interface automatically detects Pi IP address

## Hardware Requirements

- Raspberry Pi 4/5 with modern Raspberry Pi OS
- UDN2981A source driver (or similar)
- 12 LEDs with appropriate current-limiting resistors
- Network connectivity

## GPIO Pin Mapping

| FPGA | Dan (Red) | Nate (Blue) | Ben (Green) | Loaded |
|------|-----------|-------------|-------------|---------|
| FPGA 1 | GPIO 18 | GPIO 19 | GPIO 20 | GPIO 21 |
| FPGA 2 | GPIO 22 | GPIO 23 | GPIO 24 | GPIO 25 |
| FPGA 3 | GPIO 26 | GPIO 27 | GPIO 13 | GPIO 6 |

## Wiring

Raspberry Pi GPIO → UDN2981A Input → UDN2981A Output → LED → Ground

**UDN2981A Logic:**
- GPIO LOW (0V) = LED ON
- GPIO HIGH (3.3V) = LED OFF

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone 
   cd fpga-gui-new
   chmod +x install.sh
   ./install.sh

## Access web interface:

Open fpga_controller.html in any browser

Or visit http://[PI_IP]:8080/fpga_controller.html

## Test with multimeter:

  - Black probe to Pi ground

  - Red probe to GPIO pin

  - LED ON = 0V, LED OFF = 3.3v
