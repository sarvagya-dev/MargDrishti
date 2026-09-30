"""
YOLO Perception Module for MARG-DRISHTI
Standalone vehicle detection on evidence videos
"""

import cv2
from pathlib import Path
from typing import Dict, Any, List
import json


class YOLOPerception:
    """Minimal YOLO perception for vehicle detection in evidence videos."""
    
    # COCO class IDs relevant for road monitoring
    VEHICLE_CLASSES = {
        0: 'person',
        1: 'bicycle',
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck'
    }
    
    def __init__(self, model_size='yolov8n.pt'):
        """
        Initialize YOLO model.
        
        Args:
            model_size: Model variant (yolov8n.pt for nano/fastest)
        """
        try:
            from ultralytics import YOLO
            print(f"[YOLO] Loading {model_size}...")
            self.model = YOLO(model_size)
            print("[YOLO] Model loaded successfully")
        except ImportError:
            raise ImportError(
                "Ultralytics not installed. Run: pip install ultralytics torch opencv-python"
            )
    
    def analyze_video(self, video_path: str, sample_frames: int = 10) -> Dict[str, Any]:
        """
        Analyze video for vehicle detections.
        
        Args:
            video_path: Path to video file
            sample_frames: Number of frames to sample (default 10 for speed)
        
        Returns:
            Detection summary with vehicle counts and metadata
        """
        video_path = Path(video_path)
        if not video_path.exists():
            return {
                "status": "error",
                "message": f"Video not found: {video_path}"
            }
        
        print(f"[YOLO] Analyzing: {video_path.name}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {
                "status": "error",
                "message": f"Cannot open video: {video_path}"
            }
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Sample frames evenly throughout video
        if total_frames > sample_frames:
            frame_indices = [int(i * total_frames / sample_frames) for i in range(sample_frames)]
        else:
            frame_indices = list(range(total_frames))
        
        all_detections = []
        vehicle_counts = {
            'car': 0,
            'motorcycle': 0,
            'bus': 0,
            'truck': 0,
            'person': 0,
            'bicycle': 0
        }
        
        frames_analyzed = 0
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Run YOLO inference
            results = self.model(frame, verbose=False)
            
            # Process detections
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Filter for relevant classes only
                    if class_id in self.VEHICLE_CLASSES:
                        class_name = self.VEHICLE_CLASSES[class_id]
                        
                        if confidence > 0.5:  # Confidence threshold
                            all_detections.append({
                                'frame': frame_idx,
                                'class': class_name,
                                'confidence': round(confidence, 3)
                            })
                            
                            if class_name in vehicle_counts:
                                vehicle_counts[class_name] += 1
            
            frames_analyzed += 1
        
        cap.release()
        
        # Calculate statistics
        # Vehicles = cars + motorcycles + buses + trucks (NOT persons or bicycles)
        total_vehicles = (
            vehicle_counts['car'] + 
            vehicle_counts['motorcycle'] + 
            vehicle_counts['bus'] + 
            vehicle_counts['truck']
        )
        avg_confidence = (
            sum(d['confidence'] for d in all_detections) / len(all_detections)
            if all_detections else 0.0
        )
        
        print(f"[YOLO] Analyzed {frames_analyzed}/{total_frames} frames")
        print(f"[YOLO] Total detections: {len(all_detections)}")
        print(f"[YOLO] Vehicles detected: {total_vehicles}")
        
        return {
            "status": "success",
            "video_path": str(video_path),
            "video_info": {
                "total_frames": total_frames,
                "fps": fps,
                "frames_analyzed": frames_analyzed
            },
            "vehicles_detected": total_vehicles,
            "cars": vehicle_counts['car'],
            "motorcycles": vehicle_counts['motorcycle'],
            "buses": vehicle_counts['bus'],
            "trucks": vehicle_counts['truck'],
            "persons": vehicle_counts['person'],
            "bicycles": vehicle_counts['bicycle'],
            "avg_confidence": round(avg_confidence, 3),
            "detections": all_detections
        }
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze single image for vehicle detections.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Detection summary with vehicle counts
        """
        image_path = Path(image_path)
        if not image_path.exists():
            return {
                "status": "error",
                "message": f"Image not found: {image_path}"
            }
        
        print(f"[YOLO] Analyzing image: {image_path.name}")
        
        # Run YOLO inference
        results = self.model(str(image_path), verbose=False)
        
        vehicle_counts = {
            'car': 0,
            'motorcycle': 0,
            'bus': 0,
            'truck': 0,
            'person': 0,
            'bicycle': 0
        }
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if class_id in self.VEHICLE_CLASSES:
                    class_name = self.VEHICLE_CLASSES[class_id]
                    
                    if confidence > 0.5:
                        detections.append({
                            'class': class_name,
                            'confidence': round(confidence, 3)
                        })
                        
                        if class_name in vehicle_counts:
                            vehicle_counts[class_name] += 1
        
        # Calculate statistics - vehicles exclude persons and bicycles
        total_vehicles = (
            vehicle_counts['car'] + 
            vehicle_counts['motorcycle'] + 
            vehicle_counts['bus'] + 
            vehicle_counts['truck']
        )
        avg_confidence = (
            sum(d['confidence'] for d in detections) / len(detections)
            if detections else 0.0
        )
        
        print(f"[YOLO] Total detections: {len(detections)}")
        print(f"[YOLO] Vehicles detected: {total_vehicles}")
        
        return {
            "status": "success",
            "image_path": str(image_path),
            "vehicles_detected": total_vehicles,
            "cars": vehicle_counts['car'],
            "motorcycles": vehicle_counts['motorcycle'],
            "buses": vehicle_counts['bus'],
            "trucks": vehicle_counts['truck'],
            "persons": vehicle_counts['person'],
            "bicycles": vehicle_counts['bicycle'],
            "avg_confidence": round(avg_confidence, 3),
            "detections": detections
        }
    
    def save_annotated_image(self, image_path: str, output_path: str) -> str:
        """
        Save image with detection bounding boxes.
        
        Args:
            image_path: Input image path
            output_path: Output path for annotated image
        
        Returns:
            Path to saved annotated image
        """
        results = self.model(image_path, verbose=False)
        
        # Save annotated result
        for result in results:
            result.save(filename=output_path)
        
        print(f"[YOLO] Saved annotated image: {output_path}")
        return output_path
