import subprocess
import threading
import time
import logging
import socket
import requests
import cv2
import numpy as np

# ==== CONFIGURATION ====
ADB_PORT = 9999
LOCAL_PORT = 9999
UDP_IP = "127.0.0.1"
UDP_PORT = 5454
CAPTURE_URL = f"http://127.0.0.1:9998/capture"
FPS = 30
CHUNK_SIZE = 1300

# ==== LOGGER SETUP ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

class ADBManager:
    def __init__(self):
        self.running = False
        self.thread = None
        self.device_was_connected = False
        self.udp_clients = set()
        self.restream_thread = None
        self.restream_active = False

    def is_device_connected(self):
        try:
            output = subprocess.check_output(["adb", "get-state"], stderr=subprocess.DEVNULL).decode().strip()
            return output == "device"
        except:
            return False

    def setup_port_forwarding(self):
        subprocess.call(["adb", "forward", f"tcp:{LOCAL_PORT}", f"tcp:{ADB_PORT}"])
        logging.info(f"Forwarded tcp:{LOCAL_PORT} → tcp:{ADB_PORT}")

    def restart_adb(self):
        subprocess.call(["adb", "kill-server"])
        subprocess.call(["adb", "start-server"])
        logging.info("ADB server restarted")

    def mjpeg_reader(self, url):
        try:
            stream = requests.get(url, stream=True, timeout=3)
            buffer = b''
            for chunk in stream.iter_content(1024):
                buffer += chunk
                a = buffer.find(b'\xff\xd8')
                b = buffer.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = buffer[a:b+2]
                    buffer = buffer[b+2:]
                    img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        yield img
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error reading MJPEG stream: {e}")

    def restream_udp(self):
        logging.info("Starting UDP restreamer...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for frame in self.mjpeg_reader(CAPTURE_URL):
            if not self.restream_active:
                break
            _, jpeg = cv2.imencode('.jpg', frame)
            data = jpeg.tobytes()
            for i in range(0, len(data), CHUNK_SIZE):
                chunk = data[i:i+CHUNK_SIZE]
                sock.sendto(chunk, (UDP_IP, UDP_PORT))
            time.sleep(1 / FPS)
        sock.close()
        logging.info("Stopped UDP restreamer.")

    def start_restreaming(self):
        if not self.restream_active:
            self.restream_active = True
            self.restream_thread = threading.Thread(target=self.restream_udp, daemon=True)
            self.restream_thread.start()

    def stop_restreaming(self):
        if self.restream_active:
            self.restream_active = False
            if self.restream_thread:
                self.restream_thread.join()

    def monitor_loop(self):
        logging.info("ADB monitor loop started.")
        while self.running:
            connected = self.is_device_connected()

            if connected and not self.device_was_connected:
                logging.info("✅ Device connected.")
                self.setup_port_forwarding()
                self.start_restreaming()
                self.device_was_connected = True

            elif not connected and self.device_was_connected:
                logging.warning("❌ Device disconnected.")
                self.stop_restreaming()
                self.device_was_connected = False

            time.sleep(2)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logging.info("ADB Manager started.")

    def stop(self):
        self.running = False
        self.stop_restreaming()
        if self.thread:
            self.thread.join()
        logging.info("ADB Manager stopped.")
