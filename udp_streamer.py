# udp_streamer.py
import socket
import cv2
import time
import requests
import numpy as np

UDP_IP = "127.0.0.1"
UDP_PORT = 5454

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def mjpeg_reader(url):
    stream = requests.get(url, stream=True)
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

def restream_udp(url):
    for frame in mjpeg_reader(url):
        _, jpeg = cv2.imencode('.jpg', frame)
        data = jpeg.tobytes()
        for i in range(0, len(data), 1300):  # safe UDP size
            chunk = data[i:i+1300]
            sock.sendto(chunk, (UDP_IP, UDP_PORT))
        time.sleep(1/30)  # 30 fps

if __name__ == "__main__":
    source_url = "http://127.0.0.1:9999/capture"  # replace with actual IP
    restream_udp(source_url)
