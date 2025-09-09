import paho.mqtt.client as mqtt
import subprocess
import time
import logging
import signal
import sys
from threading import Lock

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/fpga_controller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# GPIO Pin Assignments - 12 LEDs total (4 per FPGA)
GPIO_PINS = {
    'fpga1': {
        'dan': 18,      # Dan's LED (Red)
        'nate': 19,     # Nate's LED (Blue)
        'ben': 20,      # Ben's LED (Green)
        'loaded': 21    # Loaded LED (Green)
    },
    'fpga2': {
        'dan': 22,      # Dan's LED (Red)
        'nate': 23,     # Nate's LED (Blue)
        'ben': 24,      # Ben's LED (Green)
        'loaded': 25    # Loaded LED (Green)
    },
    'fpga3': {
        'dan': 26,      # Dan's LED (Red)
        'nate': 27,     # Nate's LED (Blue)
        'ben': 13,      # Ben's LED (Green)
        'loaded': 6     # Loaded LED (Green)
    }
}

current_state = {
    'fpga1': {'dan': False, 'nate': False, 'ben': False, 'loaded': False},
    'fpga2': {'dan': False, 'nate': False, 'ben': False, 'loaded': False},
    'fpga3': {'dan': False, 'nate': False, 'ben': False, 'loaded': False}
}

class IndividualPinController:
    def __init__(self):
        self.mqtt_client = None
        self.running = False
        self.setup_gpio()
        signal.signal(signal.SIGINT, self.cleanup_and_exit)
        signal.signal(signal.SIGTERM, self.cleanup_and_exit)
        
    def run_pinctrl(self, command):
        """Run sudo pinctrl command"""
        try:
            cmd = f"sudo pinctrl {command}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            logger.error(f"Error running pinctrl: {e}")
            return False, ""
    
    def set_pin_output(self, pin):
        """Set pin as output"""
        success, output = self.run_pinctrl(f"set {pin} op")
        return success
    
    def set_pin_high(self, pin):
        """Set pin high (3.3V) - LED OFF for UDN2981A"""
        success, output = self.run_pinctrl(f"set {pin} dh")
        if success:
            logger.info(f"GPIO {pin} -> HIGH (3.3V) - LED OFF")
        return success
    
    def set_pin_low(self, pin):
        """Set pin low (0V) - LED ON for UDN2981A"""
        success, output = self.run_pinctrl(f"set {pin} dl")
        if success:
            logger.info(f"GPIO {pin} -> LOW (0V) - LED ON")
        return success
    
    def setup_gpio(self):
        """Initialize all GPIO pins - start with LEDs OFF"""
        logger.info("Setting up GPIO pins for UDN2981A (inverted logic):")
        for fpga_id, pins in GPIO_PINS.items():
            for led_type, pin in pins.items():
                if not self.set_pin_output(pin):
                    raise Exception(f"Failed to set GPIO {pin} as output")
                if not self.set_pin_high(pin):  # HIGH = LED OFF for UDN2981A
                    raise Exception(f"Failed to set GPIO {pin} high")
                logger.info(f"  {fpga_id} {led_type.upper()} -> GPIO {pin} (OFF)")
        logger.info("GPIO setup complete - all LEDs OFF")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("localhost", 1883, 60)
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            
            # Subscribe to all individual user command topics
            topics = []
            for fpga_id in GPIO_PINS.keys():
                for user_type in ['dan', 'nate', 'ben', 'loaded']:
                    topic = f"fpga/command/{fpga_id}/{user_type}"
                    topics.append(topic)
                    client.subscribe(topic)
            
            logger.info(f"Subscribed to {len(topics)} topics")
        else:
            logger.error(f"MQTT connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8').strip()
            logger.info(f"Received: {topic} = '{payload}'")
            
            # Parse topic: fpga/command/fpga1/dan
            parts = topic.split('/')
            if len(parts) == 4 and parts[0] == 'fpga' and parts[1] == 'command':
                fpga_id = parts[2]    # fpga1, fpga2, fpga3
                user_type = parts[3]  # dan, nate, ben, loaded
                
                if fpga_id in GPIO_PINS and user_type in GPIO_PINS[fpga_id]:
                    self.handle_pin_command(fpga_id, user_type, payload)
                    
                    # Publish status back
                    status_topic = f"fpga/status/{fpga_id}/{user_type}"
                    client.publish(status_topic, payload)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def handle_pin_command(self, fpga_id, user_type, value_str):
        """Handle individual pin command - inverted logic for UDN2981A"""
        pin = GPIO_PINS[fpga_id][user_type]
        value = value_str.lower() == 'true'
        
        # Update state
        current_state[fpga_id][user_type] = value
        
        # Control GPIO pin with inverted logic
        if value:  # Want LED ON
            self.set_pin_low(pin)   # Set GPIO LOW to turn LED ON
            logger.info(f"{fpga_id} {user_type.upper()} LED ON - GPIO {pin} LOW")
        else:      # Want LED OFF  
            self.set_pin_high(pin)  # Set GPIO HIGH to turn LED OFF
            logger.info(f"{fpga_id} {user_type.upper()} LED OFF - GPIO {pin} HIGH")
    
    def test_all_leds(self):
        """Test all LEDs individually"""
        logger.info("Testing all individual LEDs...")
        
        for fpga_id, pins in GPIO_PINS.items():
            logger.info(f"Testing {fpga_id}...")
            for user_type, pin in pins.items():
                self.set_pin_low(pin)   # LOW = LED ON for UDN2981A
                time.sleep(0.3)
                self.set_pin_high(pin)  # HIGH = LED OFF for UDN2981A
                time.sleep(0.1)
        
        logger.info("LED test complete")
    
    def cleanup_and_exit(self, signum=None, frame=None):
        """Clean shutdown - turn all LEDs OFF"""
        logger.info("Cleaning up...")
        for fpga_id, pins in GPIO_PINS.items():
            for user_type, pin in pins.items():
                self.set_pin_high(pin)  # HIGH = LED OFF for UDN2981A
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        logger.info("Cleanup complete")
        sys.exit(0)
    
    def run(self):
        """Main run loop"""
        logger.info("FPGA GPIO Controller - Individual User Pins (UDN2981A Compatible)")
        logger.info("GPIO Pin Assignments:")
        for fpga_id, pins in GPIO_PINS.items():
            pin_list = ", ".join([f"{user.upper()}={pin}" for user, pin in pins.items()])
            logger.info(f"  {fpga_id.upper()}: {pin_list}")
        
        logger.info("UDN2981A Logic: LOW=LED ON, HIGH=LED OFF")
        
        self.test_all_leds()
        self.setup_mqtt()
        self.running = True
        self.mqtt_client.loop_start()
        
        logger.info("Controller ready! Listening for commands...")
        
        try:
            while self.running:
                time.sleep(10)
        except KeyboardInterrupt:
            self.cleanup_and_exit()

if __name__ == "__main__":
    controller = IndividualPinController()
    controller.run()
