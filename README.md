# Video Streaming Pipeline

A lightweight video streaming system that converts video files into HTTP MJPEG streams and forwards them via UDP.

![Video Preview](screenshot.png)

## 🎯 Purpose

This project creates a complete video streaming pipeline:
- **HTTP Server**: Serves video as MJPEG stream over HTTP
- **UDP Streamer**: Receives HTTP stream and forwards via UDP packets
- **UDP Receiver**: Displays the UDP video stream in real-time

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the HTTP server**
   ```bash
   python server.py
   ```
   → Stream available at `http://localhost:9999/capture`

3. **Stream via UDP** (optional)
   ```bash
   python udp_streamer.py  # Forward to UDP
   python udp_receiver.py  # Receive and display
   ```

## 📁 Components

- `server.py` - HTTP MJPEG video server (30 FPS)
- `udp_streamer.py` - HTTP-to-UDP bridge
- `udp_receiver.py` - UDP video player
- `bunny.mp4` - Sample video file

## 🔧 Configuration

- **Video source**: Change `video_source` in `server.py`
- **Frame rate**: Adjust `FRAME_DELAY` (default: 30 FPS)
- **UDP settings**: Modify `UDP_IP` and `UDP_PORT` in streamer/receiver

---
*Built with Flask + OpenCV* 