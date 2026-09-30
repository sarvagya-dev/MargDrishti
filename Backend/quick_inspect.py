#!/usr/bin/env python3
"""Quick video frame inspector - minimal output"""
import cv2
import sys
from pathlib import Path

video_path = "evidence/event_1_ddd94eca23994a76b30b5dfcdc375279.webm"
if len(sys.argv) > 1:
    video_path = sys.argv[1]

video_path = Path(video_path)
cap = cv2.VideoCapture(str(video_path))

if not cap.isOpened():
    print(f"ERROR: Cannot open {video_path}")
    sys.exit(1)

# Properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

print(f"Video: {video_path.name}")
print(f"Resolution: {width}x{height}")
print(f"Frames: {frames}, FPS: {fps}, Duration: {frames/fps if fps else 0:.1f}s")

# Extract first frame
ret, frame = cap.read()
if ret:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    out_file = output_dir / f"{video_path.stem}_first_frame.jpg"
    cv2.imwrite(str(out_file), frame)
    print(f"Saved: {out_file}")
    
    # Basic analysis
    import numpy as np
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    
    print(f"Brightness: {brightness:.1f}/255", end=" ")
    if brightness < 10:
        print("(VERY DARK)")
    elif brightness < 50:
        print("(DARK)")
    elif brightness > 200:
        print("(VERY BRIGHT)")
    else:
        print("(NORMAL)")
    
    # Check color
    if frame.shape[2] == 3:
        b, g, r = cv2.split(frame)
        print(f"Color: R={r.mean():.0f}, G={g.mean():.0f}, B={b.mean():.0f}")
    
    print(f"\nOPEN THIS FILE TO SEE WHAT'S IN THE VIDEO:")
    print(f"  {out_file.absolute()}")
else:
    print("ERROR: Cannot read first frame")

cap.release()
