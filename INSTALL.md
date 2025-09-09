# Installation

Run the installation script:

    ./install.sh
Or follow the manual installation steps in INSTALL.md.

# Usage

# Turn on Dan's LED on FPGA 1

    mosquitto_pub -h localhost -t 'fpga/command/fpga1/dan' -m 'true'

# Turn off all LEDs

    mosquitto_pub -h localhost -t 'fpga/command/fpga1/dan' -m 'false'

# Service Management
 
- Check status

      sudo systemctl status fpga-controller.service

# View logs

    sudo journalctl -u fpga-controller.service -f

# Restart service

    sudo systemctl restart fpga-controller.service
