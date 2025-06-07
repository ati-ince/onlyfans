import requests
import cv2
import numpy as np
import time
import logging

# ==== CONFIG ====
MJPEG_URL = "http://127.0.0.1:9995/mjpg/video.mjpg"
RETRY_DELAY = 2  # seconds
FRAME_BOUNDARY = b"--frame"
TIMEOUT = 5  # connection timeout

# ==== LOGGER ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def http_receive_loop():
    logging.info(f"Connecting to MJPEG stream: {MJPEG_URL}")
    try:
        response = requests.get(MJPEG_URL, stream=True, timeout=TIMEOUT)
        if response.status_code != 200:
            raise ValueError(f"Bad status code: {response.status_code}")

        bytes_buffer = b""
        for chunk in response.iter_content(chunk_size=1024):
            bytes_buffer += chunk
            while True:
                start = bytes_buffer.find(b'\xff\xd8')
                end = bytes_buffer.find(b'\xff\xd9')
                if start != -1 and end != -1 and end > start:
                    jpg_data = bytes_buffer[start:end+2]
                    bytes_buffer = bytes_buffer[end+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("HTTP MJPEG Stream", frame)
                        if cv2.waitKey(1) == 27:
                            logging.info("ESC pressed. Exiting stream.")
                            return
                    else:
                        logging.warning("⚠️ Decoded frame was None.")
                else:
                    break
    except requests.exceptions.RequestException as e:
        logging.warning(f"Connection issue: {e}")
        time.sleep(RETRY_DELAY)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    while True:
        try:
            http_receive_loop()
        except Exception as err:
            logging.error(f"Retrying due to error: {err}")
            time.sleep(RETRY_DELAY)
