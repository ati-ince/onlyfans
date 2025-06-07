import socket
import cv2
import numpy as np
import time
import logging

# ==== CONFIG ====
UDP_IP = "127.0.0.1"
UDP_PORT = 5454
CHUNK_END_THRESHOLD = 1300
SOCKET_TIMEOUT = 5  # seconds
RETRY_DELAY = 1     # seconds

# ==== LOGGER ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def udp_receive_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(SOCKET_TIMEOUT)

    buffer = b""
    logging.info(f"Listening for UDP stream on {UDP_IP}:{UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(65536)
            if addr not in seen_clients:
                seen_clients.add(addr)
                logging.info(f"🎥 First data received from {addr}")

            buffer += data
            if len(data) < CHUNK_END_THRESHOLD:  # Indicates end of a JPEG frame
                frame = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow("UDP Streamed", frame)
                else:
                    logging.warning("⚠️ Decoded frame was None.")
                buffer = b""
                if cv2.waitKey(1) == 27:
                    logging.info("ESC pressed. Exiting.")
                    break
        except socket.timeout:
            logging.warning("⏳ No data received. Waiting for stream...")
            time.sleep(RETRY_DELAY)  # Continue to wait
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(RETRY_DELAY)

    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    seen_clients = set()
    while True:
        try:
            udp_receive_loop()
        except Exception as e:
            logging.error(f"Failed to receive. Retrying: {e}")
            time.sleep(RETRY_DELAY)
