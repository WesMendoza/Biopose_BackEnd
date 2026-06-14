"""
Utilidades de procesamiento de video para la Fase 3.
"""

import base64
import time
from pathlib import Path

import cv2
import numpy as np

from services.behavior_detection import BehaviorDetectionService
from services.pose_detection import PoseDetectionService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_YOLO_MODEL_PATH = PROJECT_ROOT / 'yolov8s-pose.pt'
DEFAULT_LSTM_MODEL_PATH = PROJECT_ROOT / 'resources' / 'models' / 'lstm_3clasesstride1.pt'
DEFAULT_LABEL_MAP_PATH = PROJECT_ROOT / 'resources' / 'models' / 'label_map_3clases.json'

_POSE_SERVICE = None
_BEHAVIOR_SERVICE = None

COCO_KEYPOINT_NAMES = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
]

def get_pose_service():
    global _POSE_SERVICE
    if _POSE_SERVICE is None:
        _POSE_SERVICE = PoseDetectionService(model_path=str(DEFAULT_YOLO_MODEL_PATH))
    return _POSE_SERVICE

def get_behavior_service():
    global _BEHAVIOR_SERVICE
    if _BEHAVIOR_SERVICE is None:
        _BEHAVIOR_SERVICE = BehaviorDetectionService(
            model_path=str(DEFAULT_LSTM_MODEL_PATH),
            label_map_path=str(DEFAULT_LABEL_MAP_PATH),
        )
    return _BEHAVIOR_SERVICE

# ====================================================================
# CORRECCIÓN DEFINITIVA DE CONFIANZA
# ====================================================================
def _first_person_keypoints(raw_pose_data):
    persons = raw_pose_data.get('keypoints', []) if raw_pose_data else []
    confidences = raw_pose_data.get('confidences', []) if raw_pose_data else []
    
    if not persons:
        return []

    first_person = persons[0].get('keypoints', [])
    
    # Manejo robusto de las confianzas. Si es una lista de listas, tomamos la primera.
    # Si es solo una lista plana, la tomamos entera.
    confidence_values = []
    if confidences:
        if isinstance(confidences[0], list):
            confidence_values = confidences[0]
        else:
            confidence_values = confidences

    keypoints = []
    
    for index, name in enumerate(COCO_KEYPOINT_NAMES):
        if index < len(first_person):
            point = first_person[index]
            # Si point ya tiene 3 valores (x, y, conf) desde pose_detection.py, lo usamos.
            # Esto es vital porque a veces pose_detection.py lo formatea directamente.
            if isinstance(point, (list, tuple)) and len(point) >= 3:
                x_value = float(point[0])
                y_value = float(point[1])
                confidence = float(point[2])
            else:
                x_value = float(point[0]) if len(point) > 0 else 0.0
                y_value = float(point[1]) if len(point) > 1 else 0.0
                confidence = float(confidence_values[index]) if index < len(confidence_values) else 0.0
        else:
            x_value, y_value, confidence = 0.0, 0.0, 0.0
            
        # Filtro estricto: Si la coordenada es (0,0), la confianza DEBE ser 0.0
        if x_value == 0.0 and y_value == 0.0:
            confidence = 0.0
            
        keypoints.append([x_value, y_value, confidence, name])
        
    return keypoints
# ====================================================================

def analyze_video_behavior(video_path, mode='operativo', dimension='2D', fps_skip=5, confidence_threshold=0.75):
    start_time = time.time()
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f'No se pudo abrir el video: {video_path}')

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    duration_seconds = float(total_frames / fps) if fps else 0.0

    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=25, detectShadows=False)

    sampled_keypoints = []
    sampled_frames = []
    
    fps_skip = max(1, fps_skip)
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break
            
        current_idx = frame_index
        frame_index += 1

        if current_idx % fps_skip != 0:
            continue

        frame_resized = cv2.resize(frame, (640, 640))
        fg_mask = bg_subtractor.apply(frame_resized)
        motion_level = cv2.countNonZero(fg_mask)
        
        if motion_level < 500:
            continue

        raw_pose = get_pose_service().detect_pose_frame(frame_resized)
        first_person = _first_person_keypoints(raw_pose)
        
        if len(first_person) < 17:
            continue

        sampled_frames.append({
            'frame_index': current_idx,
            'timestamp_sec': float(current_idx / fps) if fps else 0.0,
            'frame': frame_resized,
        })
        
        # GUARDAMOS TODOS LOS DATOS: [x, y, confidence, name]
        sampled_keypoints.append([[float(p[0]), float(p[1]), float(p[2]), str(p[3])] for p in first_person[:17]])

    capture.release()

    detections = []
    person_keypoints = []
    
    if sampled_keypoints:
        # LSTM solo toma X e Y
        lstm_sequence = [[[pt[0], pt[1]] for pt in frame_kps] for frame_kps in sampled_keypoints]
        sequence = np.array(lstm_sequence, dtype=np.float32)
        
        if sequence.ndim != 3 or sequence.shape[1] != 17:
            return {
                'detections': [],
                'person_keypoints': [],
                'total_frames': total_frames,
                'duration_seconds': duration_seconds,
                'processing_time_seconds': round(time.time() - start_time, 3),
                'summary': {
                    'detections_by_type': {},
                    'average_confidence': 0.0,
                    'max_confidence': 0.0,
                    'error': 'Secuencia inválida'
                },
            }
            
        if sequence.shape[0] < get_behavior_service().window_size:
            pad_count = get_behavior_service().window_size - sequence.shape[0]
            sequence = np.concatenate([sequence, np.repeat(sequence[-1][None, :, :], pad_count, axis=0)], axis=0)

        prediction = get_behavior_service().predict_behavior(sequence, confidence_threshold=confidence_threshold)
        label = prediction.get('behavior', 'UNKNOWN')
        confidence = float(prediction.get('confidence', 0.0))

        if prediction.get('is_valid') and label not in ('UNKNOWN', 'ERROR'):
            last_frame = sampled_frames[-1]
            detections.append({
                'tipo_evento': label,
                'confianza': confidence,
                'frame_inicio': sampled_frames[0]['frame_index'],
                'frame_fin': last_frame['frame_index'],
                'segundo_inicio': sampled_frames[0]['timestamp_sec'],
                'segundo_fin': last_frame['timestamp_sec'],
                'personas_involucradas': 1,
                'detalles': {'mode': mode, 'dimension': dimension, 'all_probs': prediction.get('all_probs', {})},
                'bounding_boxes': [],
                'frame_base64': '',
            })

            # CONSTRUCCIÓN FINAL DEL JSON: Usamos point[2] estrictamente
            for sf, kp in zip(sampled_frames, sampled_keypoints):
                keypoints_json = []
                for index, point in enumerate(kp):
                    keypoints_json.append({
                        'id': index,
                        'name': point[3],
                        'x': point[0],
                        'y': point[1],
                        'z': 0.0,
                        'confidence': point[2], # <--- AQUÍ SE INYECTA LA CONFIANZA PURA
                    })
                person_keypoints.append({
                    'person_id': 0,
                    'frame_index': sf['frame_index'],
                    'timestamp_sec': sf['timestamp_sec'],
                    'keypoints_json': keypoints_json,
                })

    summary = {
        'detections_by_type': {},
        'average_confidence': float(np.mean([item['confianza'] for item in detections])) if detections else 0.0,
        'max_confidence': float(np.max([item['confianza'] for item in detections])) if detections else 0.0,
    }
    for detection in detections:
        summary['detections_by_type'][detection['tipo_evento']] = summary['detections_by_type'].get(detection['tipo_evento'], 0) + 1

    return {
        'detections': detections,
        'person_keypoints': person_keypoints,
        'total_frames': total_frames,
        'duration_seconds': duration_seconds,
        'processing_time_seconds': round(time.time() - start_time, 3),
        'summary': summary,
    }

def generate_frames_from_video(video_path, fps_value=5, max_duration_seconds=30):
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f'No se pudo abrir el video: {video_path}')

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_seconds = float(total_frames / fps) if fps else 0.0
    max_frames = int(min(duration_seconds, max_duration_seconds) * fps_value)

    frames = []
    for frame_index in range(max_frames):
        timestamp_sec = frame_index / float(fps_value)
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000.0)
        ok, frame = capture.read()
        if not ok:
            continue

        ok_encode, buffer = cv2.imencode('.jpg', frame)
        if not ok_encode:
            continue

        frame_bytes = buffer.tobytes()
        frames.append({
            'frame_index': frame_index,
            'timestamp_sec': round(timestamp_sec, 3),
            'filename': f'frame_{frame_index}.jpg',
            'base64': base64.b64encode(frame_bytes).decode('utf-8'),
            'size_bytes': len(frame_bytes),
        })

    capture.release()
    return frames 