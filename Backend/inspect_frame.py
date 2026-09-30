#!/usr/bin/env python3
"""
Inspect first frame of evidence video
Extracts frame and provides visual description
"""
import cv2
import sys
from pathlib import Path

def inspect_video(video_path):
    """Extract and analyze first frame of video."""
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"ERROR: Video not found: {video_path}")
        return
    
    print(f"Inspecting: {video_path.name}")
    print("=" * 70)
    
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print("ERROR: Cannot open video")
        return
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    size_mb = video_path.stat().st_size / (1024 * 1024)
    
    print(f"\nVideo Properties:")
    print(f"  Resolution:  {width}x{height}")
    print(f"  Duration:    {duration:.1f} seconds")
    print(f"  Total frames: {total_frames}")
    print(f"  FPS:         {fps}")
    print(f"  File size:   {size_mb:.2f} MB")
    
    # Read first frame
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("\nERROR: Cannot read first frame")
        cap.release()
        return
    
    # Save first frame
    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    
    frame_filename = output_path / f"{video_path.stem}_frame0.jpg"
    cv2.imwrite(str(frame_filename), frame)
    
    print(f"\n✅ First frame extracted: {frame_filename}")
    
    # Analyze frame content
    print(f"\nFrame Analysis:")
    
    # Check if mostly black
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = gray.mean()
    print(f"  Brightness:  {mean_brightness:.1f}/255")
    
    if mean_brightness < 10:
        print(f"  Assessment:  MOSTLY BLACK/DARK")
    elif mean_brightness > 200:
        print(f"  Assessment:  MOSTLY WHITE/BRIGHT")
    else:
        print(f"  Assessment:  Normal exposure")
    
    # Color analysis
    b, g, r = cv2.split(frame)
    print(f"  Color avg:   R={r.mean():.0f}, G={g.mean():.0f}, B={b.mean():.0f}")
    
    # Edge detection to see if there's content
    edges = cv2.Canny(gray, 50, 150)
    edge_density = (edges > 0).sum() / edges.size
    print(f"  Edge density: {edge_density:.1%} (content complexity)")
    
    if edge_density < 0.01:
        print(f"  Assessment:  BLANK or VERY SIMPLE scene")
    elif edge_density > 0.15:
        print(f"  Assessment:  COMPLEX scene (high detail)")
    else:
        print(f"  Assessment:  Moderate detail")
    
    # Sample middle frame as well
    middle_frame_idx = total_frames // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_idx)
    ret, middle_frame = cap.read()
    
    if ret and middle_frame is not None:
        middle_filename = output_path / f"{video_path.stem}_frame{middle_frame_idx}.jpg"
        cv2.imwrite(str(middle_filename), middle_frame)
        print(f"\n✅ Middle frame extracted: {middle_filename}")
        
        gray_mid = cv2.cvtColor(middle_frame, cv2.COLOR_BGR2GRAY)
        print(f"  Brightness:  {gray_mid.mean():.1f}/255")
    
    cap.release()
    
    print(f"\n" + "=" * 70)
    print(f"RECOMMENDATION:")
    print(f"  1. Open and view: {frame_filename}")
    print(f"  2. Check if video shows:")
    print(f"     - Road/traffic scene with vehicles")
    print(f"     - Indoor scene with people")
    print(f"     - Dashboard/interior camera view")
    print(f"     - Blank/black frames")
    print(f"     - Other scene type")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "evidence/event_1_ddd94eca23994a76b30b5dfcdc375279.webm"
    
    inspect_video(video_path)
