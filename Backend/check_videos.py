#!/usr/bin/env python3
"""Quick script to check evidence video properties"""
import cv2
from pathlib import Path

evidence_dir = Path("evidence")
videos = sorted(evidence_dir.glob("*.webm"))

print("Evidence Videos Analysis:")
print("=" * 70)

for video_path in videos:
    cap = cv2.VideoCapture(str(video_path))
    
    if cap.isOpened():
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        size_mb = video_path.stat().st_size / (1024 * 1024)
        
        print(f"\n{video_path.name}")
        print(f"  Size:       {size_mb:.2f} MB")
        print(f"  Duration:   {duration:.1f} seconds")
        print(f"  Frames:     {total_frames}")
        print(f"  FPS:        {fps}")
        print(f"  Resolution: {width}x{height}")
        
        cap.release()
    else:
        print(f"\n{video_path.name}")
        print(f"  ERROR: Cannot open video")

print("\n" + "=" * 70)
