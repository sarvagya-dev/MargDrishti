#!/usr/bin/env python3
"""
Test YOLO perception on all evidence videos
Identifies which videos contain actual vehicles
"""
import sys
from pathlib import Path

try:
    from yolo_perception import YOLOPerception
except ImportError as e:
    print(f"ERROR: {e}")
    print("Install: pip install ultralytics torch opencv-python")
    sys.exit(1)

def main():
    evidence_dir = Path("evidence")
    videos = sorted(evidence_dir.glob("*.webm"))
    
    if not videos:
        print("No videos found in evidence/")
        return
    
    print("=" * 70)
    print("Testing YOLO Perception on All Evidence Videos")
    print("=" * 70)
    
    # Initialize YOLO once
    print("\n[1/2] Loading YOLOv8n model...")
    try:
        yolo = YOLOPerception(model_size='yolov8n.pt')
    except Exception as e:
        print(f"ERROR: Failed to load YOLO: {e}")
        return
    
    print("\n[2/2] Analyzing all videos...\n")
    
    results = []
    
    for video_path in videos:
        print(f"\nAnalyzing: {video_path.name}")
        print("-" * 70)
        
        result = yolo.analyze_video(str(video_path), sample_frames=10)
        
        if result['status'] == 'success':
            vehicles = result['vehicles_detected']
            persons = result['persons']
            total_detections = len(result['detections'])
            
            print(f"✅ Vehicles:   {vehicles} (cars: {result['cars']}, motorcycles: {result['motorcycles']}, buses: {result['buses']}, trucks: {result['trucks']})")
            print(f"   Persons:    {persons}")
            print(f"   Total detections: {total_detections}")
            print(f"   Confidence: {result['avg_confidence']:.2%}")
            
            results.append({
                'name': video_path.name,
                'vehicles': vehicles,
                'persons': persons,
                'total': total_detections,
                'confidence': result['avg_confidence']
            })
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - Best Videos for Road Vehicle Detection")
    print("=" * 70)
    
    # Sort by vehicle count
    results.sort(key=lambda x: x['vehicles'], reverse=True)
    
    if results:
        print("\nRanked by vehicle detections:")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r['name']}")
            print(f"   Vehicles: {r['vehicles']}, Persons: {r['persons']}, Total: {r['total']}, Conf: {r['confidence']:.2%}")
        
        if results[0]['vehicles'] > 0:
            print(f"\n🏆 BEST VIDEO FOR VEHICLE DETECTION:")
            print(f"   {results[0]['name']}")
            print(f"   Contains {results[0]['vehicles']} vehicle(s)")
        else:
            print(f"\n⚠️  No vehicles detected in any video")
            print(f"   All videos contain only persons or no detections")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
