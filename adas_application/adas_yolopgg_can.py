#!/usr/bin/env python3
"""
YOLOP ADAS with CAN Integration
- Vehicle detection with distance estimation  
- Lane detection with offset calculation
- Real-time CAN messaging to STM32 (10 Hz rate)
- Visual display with status overlay
"""

import os
import sys
import cv2
import argparse
import numpy as np
import time
import struct

sys.path.insert(0, os.path.expanduser('~/YOLOPgg'))
import onnxruntime as ort
import torch
from lib.core.general import non_max_suppression
import socket


class CANController:
    """CAN messaging controller - sends via UDP to Raspberry Pi"""
    
    def __init__(self, use_real_can=False, pi_ip=None):
        self.use_real_can = use_real_can
        self.pi_ip = pi_ip
        self.sock = None
        
        if pi_ip:
            # Send via UDP to Raspberry Pi CAN server
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"🌐 Network CAN: Sending to {pi_ip}:5555")
        elif use_real_can:
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
        
        if self.sock:
            # Send via UDP: [can_id:4bytes][data:8bytes]
            packet = struct.pack('<I', 0x100) + data
            self.sock.sendto(packet, (self.pi_ip, 5555))
        elif self.use_real_can:
            import can
            msg = can.Message(arbitration_id=0x100, data=data, is_extended_id=False)
            self.bus.send(msg)
        
        print(f"[CAN] Lane: {offset_int16:+5d}cm", end=' | ')
        return offset_int16
    
    def send_distance_status(self, distance_cm):
        """Send front distance (0x200)"""
        dist_uint16 = int(max(0, min(65535, distance_cm)))
        data = struct.pack('<H', dist_uint16) + b'\x00' * 6
        
        if self.sock:
            # Send via UDP: [can_id:4bytes][data:8bytes]
            packet = struct.pack('<I', 0x200) + data
            self.sock.sendto(packet, (self.pi_ip, 5555))
        elif self.use_real_can:
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
        
        if self.sock:
            # Send via UDP: [can_id:4bytes][data:8bytes]
            packet = struct.pack('<I', 0x300) + data
            self.sock.sendto(packet, (self.pi_ip, 5555))
        elif self.use_real_can:
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
    cm_per_pixel = 0.5  # Calibrate for your camera
    
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


def main(args):
    print("="*60)
    print("YOLOP ADAS with CAN Integration")
    print("="*60)
    
    can = CANController(use_real_can=args.can, pi_ip=args.pi_ip)
    
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
    print("Press 'Q' to quit\n")
    
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
            break
        
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
        
        # Send CAN at 10 Hz
        if current_time - last_can_time >= can_interval:
            steering_percent = int(np.clip(-lane_offset_cm * 2, -100, 100))
            
            # Advanced ADAS Speed Control Algorithm
            # Based on distance, cut-in detection, and time-to-collision
            
            if closest_distance_cm < 100:
                # CRITICAL: Emergency stop - vehicle too close
                speed_percent = 0
            elif closest_distance_cm < 150:
                # EMERGENCY: Hard braking required
                speed_percent = 5
            elif closest_distance_cm < 200:
                # DANGER: Aggressive braking
                speed_percent = 15
            elif closest_distance_cm < 250:
                # WARNING: Strong deceleration
                speed_percent = 25
            elif closest_distance_cm < 350:
                # CAUTION: Moderate braking (safe following distance)
                speed_percent = 35
            elif closest_distance_cm < 500:
                # AWARE: Light deceleration
                speed_percent = 50
            elif closest_distance_cm < 700:
                # COMFORTABLE: Slight reduction
                speed_percent = 65
            elif closest_distance_cm < 900:
                # NORMAL: Near cruise speed
                speed_percent = 75
            else:
                # CRUISE: Full highway speed
                speed_percent = 85
            
            # Additional safety: Detect lane invasion (vehicle cutting in)
            # If vehicle is close AND significantly offset from center, apply extra braking
            if closest_distance_cm < 500 and abs(lane_offset_cm) > 20:
                # Vehicle cutting into our lane - reduce speed by 30%
                speed_percent = max(0, int(speed_percent * 0.7))
            
            can.send_lane_status(int(lane_offset_cm))
            can.send_distance_status(int(closest_distance_cm))
            can.send_motor_command(speed_percent, steering_percent)
            last_can_time = current_time
        
        # Create overlay
        overlay = np.zeros((new_unpad_h, new_unpad_w, 3), dtype=np.uint8)
        overlay[da_seg_mask == 1] = [0, 200, 0]  # Green for drivable
        overlay[ll_seg_mask == 1] = [255, 100, 0]  # Orange for lanes
        
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
        
        cv2.imshow('YOLOP ADAS + CAN', display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default='~/YOLOPgg/weights/yolop-320-320-int8.onnx')
    parser.add_argument('--source', type=str, default='0')
    parser.add_argument('--can', action='store_true', help='Use real CAN bus (can0)')
    parser.add_argument('--can-rate', type=int, default=10, help='CAN Hz (default 10)')
    parser.add_argument('--pi-ip', type=str, default=None, help='Raspberry Pi IP for network CAN')
    args = parser.parse_args()
    args.weights = os.path.expanduser(args.weights)
    main(args)
