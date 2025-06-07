import subprocess
import threading
import time
import logging
import requests
import cv2
import numpy as np
from flask import Flask, Response

# ==== CONFIGURATION ====
ADB_PORT = 9999
LOCAL_PORT = 9999
CAPTURE_URL = "http://127.0.0.1:9998/capture"
HTTP_STREAM_PORT = 9995
HTTP_STREAM_PATH = "/mjpg/video.mjpg"
FPS = 30

# ==== LOGGER SETUP ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = Flask(__name__)
frame_lock = threading.Lock()
latest_frame = None


class ADBManager:
    def __init__(self):
        self.running = False
        self.thread = None
        self.device_was_connected = False
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
        while self.restream_active:
            try:
                stream = requests.get(url, stream=True, timeout=3)
                buffer = b''
                for chunk in stream.iter_content(1024):
                    if not self.restream_active:
                        break
                    buffer += chunk
                    a = buffer.find(b'\xff\xd8')
                    b = buffer.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = buffer[a:b+2]
                        buffer = buffer[b+2:]
                        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if img is not None:
                            global latest_frame
                            with frame_lock:
                                latest_frame = img
            except requests.exceptions.RequestException as e:
                logging.warning(f"Error reading MJPEG stream: {e}")
                time.sleep(2)

    def restream_http(self):
        logging.info(f"Starting HTTP MJPEG server on http://127.0.0.1:{HTTP_STREAM_PORT}{HTTP_STREAM_PATH}")
        app.run(host="0.0.0.0", port=HTTP_STREAM_PORT, threaded=True)

    def start_restreaming(self):
        if not self.restream_active:
            self.restream_active = True
            threading.Thread(target=self.mjpeg_reader, args=(CAPTURE_URL,), daemon=True).start()
            threading.Thread(target=self.restream_http, daemon=True).start()

    def stop_restreaming(self):
        self.restream_active = False

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


@app.route(HTTP_STREAM_PATH)
def mjpeg_feed():
    def generate():
        while True:
            with frame_lock:
                frame = latest_frame.copy() if latest_frame is not None else None
            if frame is not None:
                _, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(1 / FPS)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
