#!/usr/bin/env python3
"""
YOLO Test Script for MARG-DRISHTI
Tests YOLO perception on evidence videos
"""

import sys
import argparse
import json
from pathlib import Path

try:
    from yolo_perception import YOLOPerception
except ImportError as e:
    print(f"ERROR: {e}")
    print("\nInstall dependencies:")
    print("  pip install ultralytics torch opencv-python")
    sys.exit(1)


def print_separator(char="─", length=70):
    print(char * length)


def main():
    parser = argparse.ArgumentParser(
        description="Test YOLO vehicle detection on evidence videos"
    )
    parser.add_argument(
        "--video",
        type=str,
        help="Path to video file (e.g., evidence/event_1_xxx.webm)"
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to image file"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=10,
        help="Number of frames to sample from video (default: 10)"
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Save annotated output image"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for results (default: output)"
    )
    
    args = parser.parse_args()
    
    if not args.video and not args.image:
        print("ERROR: Specify --video or --image")
        parser.print_help()
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print_separator("=")
    print("🔍 MARG-DRISHTI YOLO Perception Test")
    print_separator("=")
    
    # Initialize YOLO
    try:
        yolo = YOLOPerception(model_size='yolov8n.pt')
    except Exception as e:
        print(f"\n❌ YOLO initialization failed: {e}")
        sys.exit(1)
    
    print()
    
    # Process video or image
    if args.video:
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"❌ Video not found: {video_path}")
            sys.exit(1)
        
        result = yolo.analyze_video(str(video_path), sample_frames=args.frames)
        
        # Save JSON result
        json_path = output_dir / f"{video_path.stem}_perception.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Saved perception data: {json_path}")
        
    elif args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            sys.exit(1)
        
        result = yolo.analyze_image(str(image_path))
        
        # Save JSON result
        json_path = output_dir / f"{image_path.stem}_perception.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Saved perception data: {json_path}")
        
        # Save annotated image if requested
        if args.annotate:
            annotated_path = output_dir / f"{image_path.stem}_annotated.jpg"
            yolo.save_annotated_image(str(image_path), str(annotated_path))
    
    # Display results
    print()
    print_separator("=")
    print("📊 DETECTION RESULTS")
    print_separator("=")
    
    if result['status'] == 'success':
        print(f"\n✅ Analysis successful")
        print(f"\n🚗 Vehicles Detected: {result['vehicles_detected']}")
        print(f"   • Cars:        {result['cars']}")
        print(f"   • Motorcycles: {result['motorcycles']}")
        print(f"   • Buses:       {result['buses']}")
        print(f"   • Trucks:      {result['trucks']}")
        print(f"   • Persons:     {result['persons']}")
        
        if 'bicycles' in result:
            print(f"   • Bicycles:    {result['bicycles']}")
        
        print(f"\n📈 Average Confidence: {result['avg_confidence']:.1%}")
        
        if args.video and 'video_info' in result:
            info = result['video_info']
            print(f"\n📹 Video Info:")
            print(f"   • Total Frames:    {info['total_frames']}")
            print(f"   • Frames Analyzed: {info['frames_analyzed']}")
            print(f"   • FPS:             {info['fps']}")
        
        print(f"\n🔍 Total Detections: {len(result['detections'])}")
        
        if result['detections'] and len(result['detections']) <= 20:
            print("\nDetection Details:")
            for i, det in enumerate(result['detections'][:10], 1):
                if 'frame' in det:
                    print(f"  {i}. {det['class']:12} (conf: {det['confidence']:.2f}, frame: {det['frame']})")
                else:
                    print(f"  {i}. {det['class']:12} (conf: {det['confidence']:.2f})")
            
            if len(result['detections']) > 10:
                print(f"  ... and {len(result['detections']) - 10} more")
        
    else:
        print(f"\n❌ Analysis failed: {result.get('message', 'Unknown error')}")
    
    print()
    print_separator("=")
    print("✅ Test complete")
    print_separator("=")


if __name__ == "__main__":
    main()
