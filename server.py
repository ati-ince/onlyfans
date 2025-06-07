from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

# Use a local video file or your webcam (0)
video_source = 'bunny.mp4'
camera = cv2.VideoCapture(video_source)

# Set desired frame rate
FRAME_DELAY = 1 / 30  # 30 FPS => 33ms per frame

def generate_mjpeg():
    while True:
        start_time = time.time()
        success, frame = camera.read()

        if not success:
            # Restart video if at the end
            camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--myboundary\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

        elapsed = time.time() - start_time
        sleep_time = FRAME_DELAY - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

@app.route('/capture')
def capture_stream():
    return Response(generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=myboundary')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9998, threaded=True)
