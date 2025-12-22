#!/usr/bin/env python3
"""
YOLOP ADAS with CAN Integration + Web Streaming
- Vehicle detection with distance estimation  
- Lane detection with offset calculation
- Real-time CAN messaging to STM32 (10 Hz rate)
- MJPEG streaming to web browser
"""

import os
import sys
import cv2
import argparse
import numpy as np
import time
import struct
from flask import Flask, Response, render_template_string
import threading

sys.path.insert(0, os.path.expanduser('~/YOLOPgg'))
import onnxruntime as ort
import torch
from lib.core.general import non_max_suppression


# Global variables for streaming
current_frame = None
frame_lock = threading.Lock()
can_status = {"lane": 0, "dist": 999, "speed": 0, "steer": 0}

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ADAS Live Stream</title>
    <style>
        body { 
            background: #1a1a1a; 
            color: #fff; 
            font-family: monospace; 
            margin: 0; 
            padding: 20px;
        }
        h1 { text-align: center; color: #0f0; }
        .container { max-width: 1200px; margin: 0 auto; }
        .video { text-align: center; margin: 20px 0; }
        .video img { max-width: 100%; border: 2px solid #0f0; }
        .status { 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 10px; 
            margin: 20px 0;
        }
        .status-item { 
            background: #2a2a2a; 
            padding: 15px; 
            border-radius: 5px; 
            text-align: center;
        }
        .status-label { color: #888; font-size: 12px; }
        .status-value { 
            color: #0f0; 
            font-size: 24px; 
            font-weight: bold; 
        }
    </style>
    <script>
        setInterval(() => {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('lane').textContent = data.lane + ' cm';
                    document.getElementById('dist').textContent = data.dist + ' cm';
                    document.getElementById('speed').textContent = data.speed + ' %';
                    document.getElementById('steer').textContent = data.steer + ' %';
                });
        }, 100);
    </script>
</head>
<body>
    <div class="container">
        <h1>🚗 ADAS Live Stream - YOLOPgg + CAN</h1>
        <div class="video">
            <img src="/video_feed" alt="ADAS Stream">
        </div>
        <div class="status">
            <div class="status-item">
                <div class="status-label">LANE OFFSET</div>
                <div class="status-value" id="lane">0 cm</div>
            </div>
            <div class="status-item">
                <div class="status-label">DISTANCE</div>
                <div class="status-value" id="dist">999 cm</div>
            </div>
            <div class="status-item">
                <div class="status-label">SPEED</div>
                <div class="status-value" id="speed">0 %</div>
            </div>
            <div class="status-item">
                <div class="status-label">STEERING</div>
                <div class="status-value" id="steer">0 %</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    return can_status

def generate_frames():
    while True:
        with frame_lock:
            if current_frame is None:
                continue
            frame = current_frame.copy()
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


class CANController:
    """CAN messaging controller"""
    
    def __init__(self, use_real_can=False):
        self.use_real_can = use_real_can
        
        if use_real_can:
            try:
                import can
                self.bus = can.interface.Bus(channel='can0', bustype='socketcan')
                print("✅ CAN bus initialized: can0")
            except Exception as e:
                print(f"⚠ CAN init failed: {e}")
                print("   Running in TEST MODE (no actual CAN)")
                self.use_real_can = False
        else:
            print("📋 TEST MODE: CAN messages printed (no actual CAN)")
    
    def send_lane_status(self, offset_cm):
        """Send lane offset (0x100)"""
        offset_int16 = int(max(-32767, min(32767, offset_cm)))
        data = struct.pack('<h', offset_int16) + b'\x00' * 6
        
        if self.use_real_can:
            import can
            msg = can.Message(arbitration_id=0x100, data=data, is_extended_id=False)
            self.bus.send(msg)
        
        print(f"[CAN] Lane: {offset_int16:+5d}cm", end=' | ')
        return offset_int16
    
    def send_distance_status(self, distance_cm):
        """Send front distance (0x200)"""
        dist_uint16 = int(max(0, min(65535, distance_cm)))
        data = struct.pack('<H', dist_uint16) + b'\x00' * 6
        
        if self.use_real_can:
            import can
            msg = can.Message(arbitration_id=0x200, data=data, is_extended_id=False)
            self.bus.send(msg)
        
        print(f"Dist: {dist_uint16:4d}cm", end=' | ')
        return dist_uint16
    
    def send_motor_command(self, speed_percent, steering_percent):
        """Send motor control (0x300)"""
        speed_int16 = int(max(-100, min(100, speed_percent)))
        steer_int16 = int(max(-100, min(100, steering_percent)))
        data = struct.pack('<hh', speed_int16, steer_int16) + b'\x00' * 4
        
        if self.use_real_can:
            import can
            msg = can.Message(arbitration_id=0x300, data=data, is_extended_id=False)
            self.bus.send(msg)
        
        print(f"Spd: {speed_int16:+4d}% Str: {steer_int16:+4d}%")
        return speed_int16, steer_int16


def calculate_distance(bbox_height, img_height, focal_length=500, real_height=1.5):
    """Calculate distance in cm using pinhole camera model"""
    if bbox_height < 10:
        return None
    return (real_height * focal_length * 100) / bbox_height


def calculate_lane_offset(lane_mask, img_width):
    """Calculate lateral offset from lane center in cm"""
    if lane_mask is None:
        return 0
    
    h, w = lane_mask.shape
    bottom_half = lane_mask[h//2:, :]
    lane_pixels = np.where(bottom_half > 0)
    
    if len(lane_pixels[1]) == 0:
        return 0
    
    lane_center = np.mean(lane_pixels[1])
    img_center = w / 2
    offset_px = lane_center - img_center
    cm_per_pixel = 0.5
    
    return offset_px * cm_per_pixel


def resize_unscale(img, new_shape=(320, 320), color=114):
    shape = img.shape[:2]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    
    canvas = np.zeros((new_shape[0], new_shape[1], 3), dtype=np.float32)
    canvas.fill(color)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    new_unpad_w = new_unpad[0]
    new_unpad_h = new_unpad[1]
    pad_w, pad_h = new_shape[1] - new_unpad_w, new_shape[0] - new_unpad_h
    dw = pad_w // 2
    dh = pad_h // 2
    
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    canvas[dh:dh + new_unpad_h, dw:dw + new_unpad_w, :] = img
    return canvas, r, dw, dh, new_unpad_w, new_unpad_h


def process_video(args, can):
    global current_frame, can_status
    
    print(f"Loading: {args.weights}")
    ort.set_default_logger_severity(3)
    ort_session = ort.InferenceSession(args.weights)
    
    input_shape = ort_session.get_inputs()[0].shape
    input_height, input_width = input_shape[2], input_shape[3]
    
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    
    cap = cv2.VideoCapture(args.source if args.source != '0' else 0)
    if not cap.isOpened():
        print(f"❌ Cannot open: {args.source}")
        return
    
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Source: {w}x{h}")
    print(f"CAN rate: {args.can_rate} Hz")
    print(f"🌐 Open browser: http://{args.host}:{args.port}")
    
    last_can_time = 0
    can_interval = 1.0 / args.can_rate
    fps_start = time.time()
    fps_counter = 0
    fps_display = 0
    
    closest_distance_cm = 999
    lane_offset_cm = 0
    speed_percent = 50
    steering_percent = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
            continue
        
        current_time = time.time()
        h, w = frame.shape[:2]
        
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas, ratio, dw, dh, new_unpad_w, new_unpad_h = resize_unscale(img_rgb, (input_height, input_width))
        
        img = canvas / 255.0
        img = (img - mean) / std
        img = img.transpose(2, 0, 1).astype(np.float32)
        img = np.expand_dims(img, axis=0)
        
        outputs = ort_session.run(None, {"images": img})
        det_out, da_seg_out, ll_seg_out = outputs
        
        det_out = torch.from_numpy(det_out).float()
        det_out = non_max_suppression(det_out, conf_thres=0.25, iou_thres=0.45)[0]
        
        boxes = det_out.cpu().numpy().astype(np.float32) if det_out is not None and len(det_out) else np.array([])
        
        if boxes.shape[0] > 0:
            boxes[:, 0] -= dw
            boxes[:, 1] -= dh
            boxes[:, 2] -= dw
            boxes[:, 3] -= dh
            boxes[:, :4] /= ratio
        
        da_seg_out = da_seg_out[:, :, dh:dh + new_unpad_h, dw:dw + new_unpad_w]
        ll_seg_out = ll_seg_out[:, :, dh:dh + new_unpad_h, dw:dw + new_unpad_w]
        
        da_seg_mask = np.argmax(da_seg_out, axis=1)[0]
        ll_seg_mask = np.argmax(ll_seg_out, axis=1)[0]
        
        ll_mask = ll_seg_mask
        lane_offset_cm = calculate_lane_offset(ll_mask, w)
        
        closest_distance_cm = 999
        if boxes.shape[0] > 0:
            for box in boxes:
                bbox_h = box[3] - box[1]
                dist_cm = calculate_distance(bbox_h, h)
                if dist_cm and dist_cm < closest_distance_cm:
                    closest_distance_cm = dist_cm
        
        # Send CAN
        if current_time - last_can_time >= can_interval:
            steering_percent = int(np.clip(-lane_offset_cm * 2, -100, 100))
            
            if closest_distance_cm < 200:
                speed_percent = 20
            elif closest_distance_cm < 500:
                speed_percent = 40
            else:
                speed_percent = 60
            
            can.send_lane_status(int(lane_offset_cm))
            can.send_distance_status(int(closest_distance_cm))
            can.send_motor_command(speed_percent, steering_percent)
            last_can_time = current_time
            
            # Update status
            can_status = {
                "lane": int(lane_offset_cm),
                "dist": int(closest_distance_cm),
                "speed": speed_percent,
                "steer": steering_percent
            }
        
        # Create overlay
        overlay = np.zeros((new_unpad_h, new_unpad_w, 3), dtype=np.uint8)
        overlay[da_seg_mask == 1] = [0, 200, 0]
        overlay[ll_seg_mask == 1] = [255, 100, 0]
        
        overlay = cv2.resize(overlay, (w, h), interpolation=cv2.INTER_LINEAR)
        display = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
        
        for i in range(boxes.shape[0]):
            x1, y1, x2, y2, conf, cls = boxes[i]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(display, f'{conf:.2f}', (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        fps_counter += 1
        if current_time - fps_start > 1.0:
            fps_display = fps_counter / (current_time - fps_start)
            fps_counter = 0
            fps_start = current_time
        
        cv2.putText(display, f'FPS: {fps_display:.1f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, f'Dist: {closest_distance_cm:.0f}cm', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(display, f'Offset: {lane_offset_cm:+.0f}cm', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(display, f'Speed: {speed_percent}%', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(display, f'Steer: {steering_percent:+d}%', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        with frame_lock:
            current_frame = display


def main(args):
    print("="*60)
    print("YOLOP ADAS with CAN Integration + Web Streaming")
    print("="*60)
    
    can = CANController(use_real_can=args.can)
    
    # Start video processing in separate thread
    video_thread = threading.Thread(target=process_video, args=(args, can), daemon=True)
    video_thread.start()
    
    # Start Flask web server
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default='~/YOLOPgg/weights/yolop-320-320-int8.onnx')
    parser.add_argument('--source', type=str, default='0')
    parser.add_argument('--can', action='store_true', help='Use real CAN bus (can0)')
    parser.add_argument('--can-rate', type=int, default=10, help='CAN Hz (default 10)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web server host')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    args = parser.parse_args()
    args.weights = os.path.expanduser(args.weights)
    main(args)
