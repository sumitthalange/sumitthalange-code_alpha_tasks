# 👁 VisionTrack – Object Detection and Tracking

A real-time computer vision project using YOLO for object detection and a lightweight centroid/SORT-style assignment tracker for persistent IDs.

## Features
- Webcam detection
- Video-file detection
- YOLOv8 Nano pretrained model
- Bounding boxes
- Object labels and confidence
- Persistent tracking IDs
- Attractive desktop GUI

## Run
```bash
pip install -r requirements.txt
python app.py
```

On the first run, Ultralytics may download `yolov8n.pt`. An internet connection is required for that first model download.

## How it works
1. Open webcam or video.
2. YOLO detects objects in each frame.
3. Low-confidence detections are filtered.
4. Object centers are calculated.
5. The tracker associates new centers with previous objects using distance + Hungarian assignment.
6. Each object receives a persistent ID while it remains trackable.

## Note
This is an educational project. The tracker is intentionally lightweight so the complete project remains easy to understand and demonstrate in a college submission.
