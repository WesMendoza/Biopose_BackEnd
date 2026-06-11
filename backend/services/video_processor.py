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


def _first_person_keypoints(raw_pose_data):
    persons = raw_pose_data.get('keypoints', []) if raw_pose_data else []
    confidences = raw_pose_data.get('confidences', []) if raw_pose_data else []
    if not persons:
        return []

    first_person = persons[0].get('keypoints', [])
    confidence_values = confidences[0] if confidences else []
    keypoints = []
    for index, name in enumerate(COCO_KEYPOINT_NAMES):
        if index < len(first_person):
            point = first_person[index]
        else:
            point = [0.0, 0.0]
        confidence = float(confidence_values[index]) if index < len(confidence_values) else 0.0
        x_value = float(point[0]) if len(point) > 0 else 0.0
        y_value = float(point[1]) if len(point) > 1 else 0.0
        keypoints.append([x_value, y_value, confidence, name])
    return keypoints


def analyze_video_behavior(video_path, mode='operativo', dimension='2D', fps_skip=5, confidence_threshold=0.75):
    start_time = time.time()
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError(f'No se pudo abrir el video: {video_path}')

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    duration_seconds = float(total_frames / fps) if fps else 0.0

    # 1. OPTIMIZACIÓN: Inicializar Motion Gating (Filtro de movimiento)
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=25, detectShadows=False)

    sequences_by_person = {}
    sampled_frames = []
    person_keypoints = []
    
    fps_skip = max(1, fps_skip)
    frame_index = 0

    # 2. OPTIMIZACIÓN: Lectura secuencial en vez de saltos con capture.set()
    while True:
        ok, frame = capture.read()
        if not ok:
            break
            
        current_idx = frame_index
        frame_index += 1

        # 3. OPTIMIZACIÓN: Frame Skipping
        if current_idx % fps_skip != 0:
            continue

        # 4. OPTIMIZACIÓN: Downscaling a la resolución de YOLO (640x640)
        frame_resized = cv2.resize(frame, (640, 640))
        
        # Aplicar el filtro de movimiento al frame pequeño
        fg_mask = bg_subtractor.apply(frame_resized)
        motion_level = cv2.countNonZero(fg_mask)
        
        # Si casi no hay movimiento (menos de 500 pixeles de 640x640), saltar a YOLO
        if motion_level < 500:
            continue

        timestamp_sec = float(current_idx / fps) if fps else 0.0

        # RASTREO MULTI-PERSONA CON BYTETRACK
        tracking_data = get_pose_service().detect_pose_with_tracking(frame_resized, persist=True)
        tracked_persons = tracking_data.get('tracked_persons', [])
        
        if not tracked_persons:
            continue

        sampled_frames.append({
            'frame_index': current_idx,
            'timestamp_sec': timestamp_sec,
            'frame': frame_resized,
        })

        for person in tracked_persons:
            p_id = person.get('person_id', 0)
            p_kps = person.get('keypoints', [])
            
            if len(p_kps) >= 17:
                kps_xy = [[float(point[0]), float(point[1])] for point in p_kps[:17]]
                
                if p_id not in sequences_by_person:
                    sequences_by_person[p_id] = []
                    
                sequences_by_person[p_id].append({
                    'frame_index': current_idx,
                    'timestamp_sec': timestamp_sec,
                    'keypoints': kps_xy
                })
                
                keypoints_json = []
                for index, point in enumerate(kps_xy):
                    keypoints_json.append({
                        'id': index,
                        'name': COCO_KEYPOINT_NAMES[index],
                        'x': point[0],
                        'y': point[1],
                        'z': 0.0,
                        'confidence': 1.0, 
                    })
                    
                person_keypoints.append({
                    'person_id': p_id,
                    'frame_index': current_idx,
                    'timestamp_sec': timestamp_sec,
                    'keypoints_json': keypoints_json,
                })

    capture.release()

    detections = []
    
    # 5. INFERENCIA LSTM INDEPENDIENTE POR CADA PERSONA
    for p_id, seq_data in sequences_by_person.items():
        if not seq_data:
            continue
            
        sequence_np = np.array([item['keypoints'] for item in seq_data], dtype=np.float32)
        if sequence_np.ndim != 3 or sequence_np.shape[1] != 17:
            continue
            
        if sequence_np.shape[0] < get_behavior_service().window_size:
            pad_count = get_behavior_service().window_size - sequence_np.shape[0]
            sequence_np = np.concatenate([sequence_np, np.repeat(sequence_np[-1][None, :, :], pad_count, axis=0)], axis=0)

        prediction = get_behavior_service().predict_behavior(sequence_np, confidence_threshold=confidence_threshold)
        label = prediction.get('behavior', 'UNKNOWN')
        confidence = float(prediction.get('confidence', 0.0))

        if prediction.get('is_valid') and label not in ('UNKNOWN', 'ERROR', 'Normal'):
            detections.append({
                'tipo_evento': label,
                'confianza': confidence,
                'frame_inicio': seq_data[0]['frame_index'],
                'frame_fin': seq_data[-1]['frame_index'],
                'segundo_inicio': seq_data[0]['timestamp_sec'],
                'segundo_fin': seq_data[-1]['timestamp_sec'],
                'personas_involucradas': len(sequences_by_person),
                'detalles': {
                    'mode': mode,
                    'dimension': dimension,
                    'all_probs': prediction.get('all_probs', {}),
                    'trigger_person_id': p_id
                },
                'bounding_boxes': [],
                'frame_base64': '',
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
