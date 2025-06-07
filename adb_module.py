import subprocess
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

class ADBManager:
    def __init__(self, adb_port=9999, local_port=9999):
        self.adb_port = adb_port
        self.local_port = local_port
        self.running = False
        self.thread = None
        self.device_was_connected = False

    def is_device_connected(self):
        try:
            output = subprocess.check_output(["adb", "get-state"], stderr=subprocess.DEVNULL).decode().strip()
            return output == "device"
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            logging.error("ADB binary not found. Ensure 'adb' is installed and in your PATH.")
            return False

    def setup_port_forwarding(self):
        subprocess.call(["adb", "forward", f"tcp:{self.local_port}", f"tcp:{self.adb_port}"])
        logging.info(f"Forwarded tcp:{self.local_port} → tcp:{self.adb_port}")

    def restart_adb(self):
        subprocess.call(["adb", "kill-server"])
        subprocess.call(["adb", "start-server"])
        logging.info("ADB server restarted")

    def monitor_loop(self):
        logging.info("Starting ADB monitor loop...")
        while self.running:
            connected = self.is_device_connected()

            if connected and not self.device_was_connected:
                logging.info("✅ Device connected")
                self.setup_port_forwarding()
                self.device_was_connected = True

            elif not connected and self.device_was_connected:
                logging.warning("❌ Device disconnected")
                self.device_was_connected = False

            time.sleep(2)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logging.info("ADB Manager thread started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        logging.info("ADB Manager stopped")
