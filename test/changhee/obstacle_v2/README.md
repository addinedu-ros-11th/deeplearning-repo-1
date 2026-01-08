# Obstacle Detector v2 (YOLO Track + Risk Engine)

## What it does
- Track Cart/Person with Track IDs
- Compute SAFE/CAUTION/WARN based on approach + center + proxy TTC
- Log WARN events to CSV and save snapshots
- Optionally save annotated video

## Install
pip install -r requirements.txt

## Run (webcam)
python run_webcam.py --config config.yaml --source 0 --show --save_video

Quit: press 'q'
