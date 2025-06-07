# udp_receiver.py
import socket
import cv2
import numpy as np

UDP_IP = "0.0.0.0"
UDP_PORT = 5454

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(5)

buffer = b""

while True:
    try:
        data, _ = sock.recvfrom(65536)
        buffer += data
        if len(data) < 1300:  # end of frame signal
            frame = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("UDP Streamed", frame)
            buffer = b""
            if cv2.waitKey(1) == 27:
                break
    except socket.timeout:
        print("Socket timeout.")
        break

sock.close()
cv2.destroyAllWindows()
