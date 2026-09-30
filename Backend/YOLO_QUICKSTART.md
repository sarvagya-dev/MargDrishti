# YOLO Perception - Quick Start

## Installation

```bash
cd Backend
pip install -r requirements-yolo.txt
```

**Note:** First run will download YOLOv8n model (~6MB) automatically.

## Test on Evidence Video

```bash
python test_yolo.py --video evidence/event_1_ddd94eca23994a76b30b5dfcdc375279.webm
```

## Expected Output

```
✅ Analysis successful

🚗 Vehicles Detected: 5
   • Cars:        3
   • Motorcycles: 2
   • Buses:       0
   • Trucks:      0

📈 Average Confidence: 87%
```

## Output Files

- `output/<filename>_perception.json` - Detection metadata
- `output/<filename>_annotated.jpg` - Image with bounding boxes (use --annotate flag)

## Options

```bash
# Analyze video with 20 frame samples
python test_yolo.py --video evidence/video.webm --frames 20

# Analyze image
python test_yolo.py --image test.jpg --annotate

# Custom output directory
python test_yolo.py --video evidence/video.webm --output results
```

## Troubleshooting

**Import Error:**
```bash
pip install ultralytics torch opencv-python
```

**Model Download Issues:**
- Requires internet connection on first run
- Model cached at: `~/.cache/torch/hub/`
