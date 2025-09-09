#!/bin/bash
# FPGA GPIO Controller Installation Script
# Automated setup for Raspberry Pi

set -e  # Exit on any error

echo "=========================================="
echo "FPGA GPIO Controller Installation"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "❌ Don't run this script as root! Run as regular user (pi)"
  exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Updating system packages..."
sudo apt update

echo "📦 Installing required packages..."
sudo apt install -y python3 python3-pip python3-paho-mqtt mosquitto mosquitto-clients

echo "🛑 Stopping mosquitto if running..."
sudo systemctl stop mosquitto 2>/dev/null || true

echo "⚙️  Configuring MQTT broker..."
sudo tee /etc/mosquitto/mosquitto.conf > /dev/null <<EOF
allow_anonymous true
listener 1883 0.0.0.0
protocol mqtt
listener 9001 0.0.0.0  
protocol websockets
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
EOF

echo "🔧 Creating mosquitto directories..."
sudo mkdir -p /var/log/mosquitto /var/lib/mosquitto

echo "🔧 Fixing mosquitto service..."
sudo tee /etc/systemd/system/mosquitto.service > /dev/null <<EOF
[Unit]
Description=Mosquitto MQTT Broker
After=network.target

[Service]
Type=notify
NotifyAccess=main
ExecStart=/usr/sbin/mosquitto -c /etc/mosquitto/mosquitto.conf
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "▶️  Starting MQTT broker..."
sudo systemctl daemon-reload
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Wait for mosquitto to start
sleep 2

echo "🧪 Testing MQTT broker..."
if sudo systemctl is-active --quiet mosquitto; then
    echo "✅ MQTT broker is running"
    
    # Test MQTT functionality
    timeout 3s mosquitto_sub -h localhost -t test &
    sleep 1
    mosquitto_pub -h localhost -t test -m "test message"
    sleep 1
    echo "✅ MQTT test complete"
else
    echo "❌ MQTT broker failed to start"
    sudo systemctl status mosquitto
    exit 1
fi

echo "📁 Setting up project directory..."
mkdir -p ~/fpga_controller
cd ~/fpga_controller

# Check if files exist in current directory (for git cloned repo)
if [ -f "../fpga_gpio_controller.py" ]; then
    echo "📋 Copying files from repository..."
    cp ../fpga_gpio_controller.py .
    cp ../fpga_controller.html .
    if [ -f "../scripts/start_webserver.py" ]; then
        cp ../scripts/start_webserver.py .
    fi
else
    echo "⚠️  Project files not found in parent directory"
    echo "Please ensure you've cloned the repository and run this script from within it"
    exit 1
fi

echo "🔧 Setting file permissions..."
chmod +x fpga_gpio_controller.py
if [ -f "start_webserver.py" ]; then
    chmod +x start_webserver.py
fi

echo "🧪 Testing GPIO with pinctrl..."
if command -v pinctrl &> /dev/null; then
    echo "✅ pinctrl is available"
    
    # Test a few pins
    for pin in 18 19 20 21; do
        if sudo pinctrl set $pin op && sudo pinctrl set $pin dh && sudo pinctrl set $pin dl; then
            echo "✅ GPIO $pin test passed"
        else
            echo "❌ GPIO $pin test failed"
            exit 1
        fi
    done
else
    echo "❌ pinctrl command not found!"
    echo "Please ensure you're running on a modern Raspberry Pi OS"
    exit 1
fi

echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/fpga-controller.service > /dev/null <<EOF
[Unit]
Description=FPGA GPIO Controller
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/fpga_controller
ExecStart=/usr/bin/python3 /home/pi/fpga_controller/fpga_gpio_controller.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "▶️  Enabling and starting controller service..."
sudo systemctl daemon-reload
sudo systemctl enable fpga-controller.service
sudo systemctl start fpga-controller.service

# Wait for service to start
sleep 3

echo "🔍 Checking service status..."
if sudo systemctl is-active --quiet fpga-controller.service; then
    echo "✅ FPGA Controller service is running"
else
    echo "❌ FPGA Controller service failed to start"
    echo "Check logs with: sudo journalctl -u fpga-controller.service"
    exit 1
fi

echo "🧪 Testing complete system..."
echo "Sending test MQTT command..."
mosquitto_pub -h localhost -t 'fpga/command/fpga1/dan' -m 'true'
sleep 1
mosquitto_pub -h localhost -t 'fpga/command/fpga1/dan' -m 'false'

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📍 GPIO Pin Assignments:"
echo "  FPGA 1: Dan=18, Nate=19, Ben=20, Loaded=21"
echo "  FPGA 2: Dan=22, Nate=23, Ben=24, Loaded=25" 
echo "  FPGA 3: Dan=26, Nate=27, Ben=13, Loaded=6"
echo ""
echo "🔌 Hardware Setup:"
echo "  GPIO Pin → UDN2981A Input → UDN2981A Output → LED → Ground"
echo "  Logic: GPIO LOW (0V) = LED ON, GPIO HIGH (3.3V) = LED OFF"
echo ""
echo "🌐 Web Interface:"
echo "  • Open fpga_controller.html in any browser"
echo "  • Or start web server: python3 start_webserver.py"
echo "  • Then visit: http://$(hostname -I | awk '{print $1}'):8080/"
echo ""
echo "📊 Service Management:"
echo "  • Check status: sudo systemctl status fpga-controller.service"
echo "  • View logs: sudo journalctl -u fpga-controller.service -f"
echo "  • Restart: sudo systemctl restart fpga-controller.service"
echo ""
echo "🧪 Testing:"
echo "  • Manual test: mosquitto_pub -h localhost -t 'fpga/command/fpga1/dan' -m 'true'"
echo "  • Multimeter: LED ON = 0V, LED OFF = 3.3V"
echo ""
echo "❓ Need help? Check TROUBLESHOOTING.md"
