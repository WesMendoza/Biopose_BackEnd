"""
Utilidades de procesamiento de video para la Fase 3.
Motor Híbrido: YOLOv8-pose (2D) y MediaPipe (3D)
"""

import os
import base64
import time
from pathlib import Path

import cv2
import numpy as np
from collections import deque

from services.behavior_detection import BehaviorDetectionService
from services.pose_detection import PoseDetectionService
from services.mediapipe_detection import MediaPipePoseService  # <--- NUEVO SERVICIO 3D

# ====================================================================
# BLINDAJE DE RUTAS PARA CELERY
# ====================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'yolov8s-pose.pt')
DEFAULT_LSTM_MODEL_PATH = os.path.join(BASE_DIR, 'resources', 'models', 'lstm_3clasesstride1.pt')
DEFAULT_LABEL_MAP_PATH = os.path.join(BASE_DIR, 'resources', 'models', 'label_map_3clases.json')

if not os.path.exists(DEFAULT_YOLO_MODEL_PATH):
    print(f"❌ ERROR FATAL: YOLO no encontrado en {DEFAULT_YOLO_MODEL_PATH}")
if not os.path.exists(DEFAULT_LSTM_MODEL_PATH):
    print(f"❌ ERROR FATAL: LSTM no encontrado en {DEFAULT_LSTM_MODEL_PATH}")
# ====================================================================

_POSE_SERVICE = None
_MP_POSE_SERVICE = None  # <--- SINGLETON 3D
_BEHAVIOR_SERVICE = None

COCO_KEYPOINT_NAMES = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
]

def get_pose_service():
    global _POSE_SERVICE
    if _POSE_SERVICE is None: _POSE_SERVICE = PoseDetectionService(model_path=str(DEFAULT_YOLO_MODEL_PATH))
    return _POSE_SERVICE

def get_mp_pose_service():
    global _MP_POSE_SERVICE
    if _MP_POSE_SERVICE is None: _MP_POSE_SERVICE = MediaPipePoseService()
    return _MP_POSE_SERVICE

def get_behavior_service():
    global _BEHAVIOR_SERVICE
    if _BEHAVIOR_SERVICE is None:
        _BEHAVIOR_SERVICE = BehaviorDetectionService(
            model_path=str(DEFAULT_LSTM_MODEL_PATH), label_map_path=str(DEFAULT_LABEL_MAP_PATH),
        )
    return _BEHAVIOR_SERVICE

# ====================================================================
# LÓGICA HEURÍSTICA DE COMPORTAMIENTOS ESPECÍFICOS
# Formato esperado de kp: [x, y, z, confianza, nombre]
# ====================================================================

def detectar_manos_ocultas_o_armas(frame_kps, usar_3d):
    """
    Si usar_3d es True, usamos el Eje Z para saber si la mano está intersectando 
    el cuerpo (Z cercana a 0) o escondida detrás (Z fuertemente positiva).
    Si es 2D, usamos la lógica de descarte por confianza de YOLO.
    """
    try:
        hombro_izq, hombro_der = frame_kps[5], frame_kps[6]
        muneca_izq, muneca_der = frame_kps[9], frame_kps[10]

        if usar_3d:
            # Índice 2 es el eje Z
            z_hombro_promedio = (hombro_izq[2] + hombro_der[2]) / 2
            
            # En MediaPipe, Z negativa es hacia la cámara, Z positiva es alejándose.
            mano_escondida_espalda = (muneca_izq[2] > z_hombro_promedio + 0.15) or \
                                     (muneca_der[2] > z_hombro_promedio + 0.15)
            return mano_escondida_espalda
        else:
            # Índice 3 es la confianza. Lógica 2D original
            hombros_visibles = hombro_izq[3] > 0.5 and hombro_der[3] > 0.5
            munecas_ocultas = (muneca_izq[3] < 0.3 or (muneca_izq[0] == 0 and muneca_izq[1] == 0)) and \
                              (muneca_der[3] < 0.3 or (muneca_der[0] == 0 and muneca_der[1] == 0))

            return hombros_visibles and munecas_ocultas
    except IndexError:
        return False

def detectar_mano_bajo_ropa(frame_kps):
    """
    Crea un polígono entre hombros y cadera, y revisa si la muñeca está dentro.
    """
    try:
        hombro_izq, hombro_der = frame_kps[5], frame_kps[6]
        cadera_izq, cadera_der = frame_kps[11], frame_kps[12]
        muneca_izq, muneca_der = frame_kps[9], frame_kps[10]

        # Validamos con la confianza (Índice 3)
        if any(kp[3] < 0.5 for kp in [hombro_izq, hombro_der, cadera_izq, cadera_der]):
            return False

        min_x = min(hombro_izq[0], hombro_der[0], cadera_izq[0], cadera_der[0])
        max_x = max(hombro_izq[0], hombro_der[0], cadera_izq[0], cadera_der[0])
        min_y = min(hombro_izq[1], hombro_der[1]) 
        max_y = max(cadera_izq[1], cadera_der[1]) 

        mano_izq_dentro = (muneca_izq[3] > 0.4) and (min_x <= muneca_izq[0] <= max_x) and (min_y <= muneca_izq[1] <= max_y)
        mano_der_dentro = (muneca_der[3] > 0.4) and (min_x <= muneca_der[0] <= max_x) and (min_y <= muneca_der[1] <= max_y)

        return mano_izq_dentro or mano_der_dentro
    except IndexError:
        return False

def detectar_mirada_excesiva(frame_kps_history):
    """
    Evalúa la varianza del vector nariz-cuello en los últimos N frames.
    """
    if len(frame_kps_history) < 10:
        return False
        
    angulos = []
    for f_kps in frame_kps_history:
        try:
            nariz, hombro_izq, hombro_der = f_kps[0], f_kps[5], f_kps[6]
            if nariz[3] < 0.5 or hombro_izq[3] < 0.5 or hombro_der[3] < 0.5:
                continue
                
            centro_cuello_x = (hombro_izq[0] + hombro_der[0]) / 2
            centro_cuello_y = (hombro_izq[1] + hombro_der[1]) / 2
            
            angulo = np.arctan2(nariz[1] - centro_cuello_y, nariz[0] - centro_cuello_x)
            angulos.append(angulo)
        except IndexError:
            continue
            
    if len(angulos) < 10:
        return False
        
    varianza = np.var(angulos[-10:])
    return varianza < 0.005


# ====================================================================
# BUCLE PRINCIPAL DE PROCESAMIENTO DE VIDEO
# ====================================================================

def analyze_video_multipersona(video_path, mode='operativo', dimension='2D', fps_skip=5, confidence_threshold=0.75):
    start_time = time.time()
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened(): raise ValueError(f'No se pudo abrir el video: {video_path}')

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    duration_seconds = float(total_frames / fps) if fps else 0.0

    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=25, detectShadows=False)

    sampled_frames = []
    lstm_global_sequence = []
    
    fps_skip = 1 if mode in ['analitico', 'debug'] else max(1, int(fps_skip))
    usar_3d = (dimension == '3D')
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok: break
        
        current_idx = frame_index
        frame_index += 1

        if current_idx % fps_skip != 0: continue

        frame_resized = cv2.resize(frame, (640, 640))
        
        if mode != 'debug':
            fg_mask = bg_subtractor.apply(frame_resized)
            if cv2.countNonZero(fg_mask) < 500: continue

        current_frame_people = []

        if usar_3d:
            raw_pose_mp = get_mp_pose_service().detect_pose_frame_3d(frame_resized)
            for p_idx, p_data in enumerate(raw_pose_mp):
                if len(p_data) >= 17:
                    kps = [[float(pt[0]), float(pt[1]), float(pt[2]), float(pt[3]), str(COCO_KEYPOINT_NAMES[i])] for i, pt in enumerate(p_data[:17])]
                    current_frame_people.append({'person_id': p_idx, 'keypoints': kps})
        else:
            raw_pose = get_pose_service().detect_pose_frame(frame_resized)
            kps_crudos = raw_pose.get('keypoints', []) if raw_pose else []
            confidencias = raw_pose.get('confidences', []) if raw_pose else []
            
            for p_idx, p_coords in enumerate(kps_crudos):
                coords = p_coords.get('keypoints', [])
                confs = confidencias[p_idx] if p_idx < len(confidencias) else []
                kps = []
                for i in range(17):
                    x, y = coords[i] if i < len(coords) else (0.0, 0.0)
                    c = confs[i] if i < len(confs) else 0.0
                    kps.append([float(x), float(y), 0.0, float(c), str(COCO_KEYPOINT_NAMES[i])])
                
                if len(kps) >= 17:
                    current_frame_people.append({'person_id': p_idx, 'keypoints': kps})

        if current_frame_people:
            sampled_frames.append({
                'frame_index': current_idx,
                'timestamp_sec': float(current_idx / fps) if fps else 0.0,
                'persons': current_frame_people
            })
            lstm_global_sequence.append(current_frame_people[0]['keypoints'])

    capture.release()

    detections = []
    
    if lstm_global_sequence:
        if usar_3d: sequence_data = [[[pt[0], pt[1], pt[2]] for pt in frame_kps] for frame_kps in lstm_global_sequence]
        else: sequence_data = [[[pt[0], pt[1]] for pt in frame_kps] for frame_kps in lstm_global_sequence]
             
        sequence = np.array(sequence_data, dtype=np.float32)
        coordenadas = 3 if usar_3d else 2
        
        window_size = get_behavior_service().window_size
        step = window_size // 2

        if sequence.ndim == 3 and sequence.shape[1] == 17 and sequence.shape[2] == coordenadas:
            for start_idx in range(0, sequence.shape[0], step):
                window = sequence[start_idx : start_idx + window_size]
                
                if window.shape[0] < window_size:
                    pad_count = window_size - window.shape[0]
                    window = np.concatenate([window, np.repeat(window[-1][None, :, :], pad_count, axis=0)], axis=0)

                try:
                    prediction = get_behavior_service().predict_behavior(window, confidence_threshold=confidence_threshold)
                    label = prediction.get('behavior', 'UNKNOWN')
                    conf = float(prediction.get('confidence', 0.0))

                    if label in ['PELEAR', 'DISTURBIO', 'FIGHT', 'DISTURBANCE']:
                        idx_inicio = min(start_idx, len(sampled_frames)-1)
                        idx_fin = min(start_idx + window.shape[0] - 1, len(sampled_frames)-1)
                        
                        first_f = sampled_frames[idx_inicio]
                        last_f = sampled_frames[idx_fin]
                        
                        detections.append({
                            'tipo_evento': label,
                            'confianza': conf,
                            'frame_inicio': first_f['frame_index'],
                            'frame_fin': last_f['frame_index'],
                            'segundo_inicio': first_f['timestamp_sec'],
                            'segundo_fin': last_f['timestamp_sec'],
                            'personas_involucradas': len(first_f['persons']),
                            'detalles': {'mode': mode, 'dimension': dimension},
                        })
                except Exception as e:
                    print(f"Error LSTM: {e}")

    frames_data_json = []
    for sf in sampled_frames:
        persons_json = []
        for p in sf['persons']:
            kps_formateados = [{'id': idx, 'name': pt[4], 'x': pt[0], 'y': pt[1], 'z': pt[2], 'confidence': pt[3]} for idx, pt in enumerate(p['keypoints'])]
            persons_json.append({'person_id': p['person_id'], 'keypoints_json': kps_formateados})
        frames_data_json.append({'frame_index': sf['frame_index'], 'timestamp_sec': sf['timestamp_sec'], 'persons': persons_json})

    summary = {
        'detections_by_type': {},
        'average_confidence': float(np.mean([item['confianza'] for item in detections])) if detections else 0.0,
    }
    for d in detections:
        summary['detections_by_type'][d['tipo_evento']] = summary['detections_by_type'].get(d['tipo_evento'], 0) + 1

    return {
        'detections': detections,
        'frames_data': frames_data_json,
        'total_frames': total_frames,
        'duration_seconds': duration_seconds,
        'processing_time_seconds': round(time.time() - start_time, 3),
        'summary': summary,
    }

def analyze_video_individual(video_path, mode='operativo', dimension='2D', fps_skip=5, confidence_threshold=0.75):
    start_time = time.time()
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened(): raise ValueError(f'No se pudo abrir el video: {video_path}')

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    duration_seconds = float(total_frames / fps) if fps else 0.0

    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=25, detectShadows=False)

    sampled_frames = []
    detections = []
    frame_kps_history = deque(maxlen=30)
    
    fps_skip = 1 if mode in ['analitico', 'debug'] else max(1, int(fps_skip))
    usar_3d = (dimension == '3D')
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok: break
        
        current_idx = frame_index
        frame_index += 1

        if current_idx % fps_skip != 0: continue

        frame_resized = cv2.resize(frame, (640, 640))
        
        if mode != 'debug':
            fg_mask = bg_subtractor.apply(frame_resized)
            if cv2.countNonZero(fg_mask) < 500: continue

        current_frame_people = []

        if usar_3d:
            raw_pose_mp = get_mp_pose_service().detect_pose_frame_3d(frame_resized)
            for p_idx, p_data in enumerate(raw_pose_mp):
                if len(p_data) >= 17:
                    kps = [[float(pt[0]), float(pt[1]), float(pt[2]), float(pt[3]), str(COCO_KEYPOINT_NAMES[i])] for i, pt in enumerate(p_data[:17])]
                    current_frame_people.append({'person_id': p_idx, 'keypoints': kps})
        else:
            raw_pose = get_pose_service().detect_pose_frame(frame_resized)
            kps_crudos = raw_pose.get('keypoints', []) if raw_pose else []
            confidencias = raw_pose.get('confidences', []) if raw_pose else []
            
            for p_idx, p_coords in enumerate(kps_crudos):
                coords = p_coords.get('keypoints', [])
                confs = confidencias[p_idx] if p_idx < len(confidencias) else []
                kps = []
                for i in range(17):
                    x, y = coords[i] if i < len(coords) else (0.0, 0.0)
                    c = confs[i] if i < len(confs) else 0.0
                    kps.append([float(x), float(y), 0.0, float(c), str(COCO_KEYPOINT_NAMES[i])])
                
                if len(kps) >= 17:
                    current_frame_people.append({'person_id': p_idx, 'keypoints': kps})

        if current_frame_people:
            timestamp_sec = float(current_idx / fps) if fps else 0.0
            sampled_frames.append({
                'frame_index': current_idx,
                'timestamp_sec': timestamp_sec,
                'persons': current_frame_people
            })
            
            for persona in current_frame_people:
                kps = persona['keypoints']
                frame_kps_history.append(kps)
                
                if detectar_mano_bajo_ropa(kps):
                    detections.append({
                        'tipo_evento': 'hand_under_clothes',
                        'confianza': 0.8,
                        'frame_inicio': current_idx,
                        'frame_fin': current_idx,
                        'segundo_inicio': timestamp_sec,
                        'segundo_fin': timestamp_sec,
                        'personas_involucradas': 1,
                        'detalles': {'mode': mode, 'razon': 'muñeca intersecta torso'}
                    })
                
                if detectar_mirada_excesiva(frame_kps_history):
                    detections.append({
                        'tipo_evento': 'excessive_gaze',
                        'confianza': 0.9,
                        'frame_inicio': current_idx,
                        'frame_fin': current_idx,
                        'segundo_inicio': timestamp_sec,
                        'segundo_fin': timestamp_sec,
                        'personas_involucradas': 1,
                        'detalles': {'mode': mode, 'razon': 'baja varianza en vector cuello-nariz'}
                    })

    capture.release()

    frames_data_json = []
    for sf in sampled_frames:
        persons_json = []
        for p in sf['persons']:
            kps_formateados = [{'id': idx, 'name': pt[4], 'x': pt[0], 'y': pt[1], 'z': pt[2], 'confidence': pt[3]} for idx, pt in enumerate(p['keypoints'])]
            persons_json.append({'person_id': p['person_id'], 'keypoints_json': kps_formateados})
        frames_data_json.append({'frame_index': sf['frame_index'], 'timestamp_sec': sf['timestamp_sec'], 'persons': persons_json})

    summary = {
        'detections_by_type': {},
        'average_confidence': float(np.mean([item['confianza'] for item in detections])) if detections else 0.0,
    }
    for d in detections:
        summary['detections_by_type'][d['tipo_evento']] = summary['detections_by_type'].get(d['tipo_evento'], 0) + 1

    return {
        'detections': detections,
        'frames_data': frames_data_json,
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