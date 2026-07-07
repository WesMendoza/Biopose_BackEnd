"""
Servicio de procesamiento en vivo de frames para detección de acciones multipersona.
Migrado desde: main.py -> live_actions_remote
Basado en la lógica del motor híbrido (Fase 3): YOLOv8-pose y MediaPipe.
"""

import cv2
import numpy as np
import base64
from collections import deque

from services.behavior_detection import BehaviorDetectionService
from services.pose_detection import PoseDetectionService
from services.mediapipe_detection import MediaPipePoseService
from services.video_processor import get_pose_service, get_mp_pose_service, get_behavior_service, COCO_KEYPOINT_NAMES

class LiveActionMultiPersonProcessor:
    def __init__(self, frame_skip=3, mode='operativo', dimension='2D'):
        self.frame_skip = max(1, int(frame_skip))
        self.mode = mode
        self.dimension = dimension
        self.usar_3d = (dimension == '3D')
        self.frame_counter = 0
        self.fps_estimate = 30.0

        # Parámetros para la máquina de estados LSTM
        self.WINDOW_SIZE = get_behavior_service().window_size
        self.EVAL_WINDOW = 15
        self.MIN_P = 5
        self.MIN_D = 5
        self.END_W = 10
        self.ESCAPE_D = 10

        # Estado acumulado
        self.buffers = {}
        self.states_history = {}
        self.reporte_eventos = []
        
        self.all_detections = []
        self.realtime_unique_behaviors = set()

    def process_frame(self, frame, overlay_only=False):
        """
        Procesa un frame BGR de OpenCV.
        Retorna: (output_frame_bgr, behaviors_list, num_people)
        """
        self.frame_counter += 1
        
        # En 'operativo' el background subtractor normalmente limpia el fondo. 
        # Aquí para simplificar, usaremos el frame directo pero consideraremos el skip rate
        process_this = (self.frame_skip == 0) or (self.frame_counter % self.frame_skip == 0)

        if overlay_only:
            output_frame = np.zeros_like(frame)
        else:
            output_frame = frame.copy()
            
        behaviors_detected = []
        num_people = 0

        if not process_this:
            return output_frame, behaviors_detected, num_people

        # Redimensionar frame para consistencia con el modelo
        frame_resized = cv2.resize(frame, (640, 640))
        current_frame_people = []
        current_time = self.frame_counter / self.fps_estimate

        # Extraer poses
        if self.usar_3d:
            raw_pose_mp = get_mp_pose_service().detect_pose_frame_3d(frame_resized)
            for p_idx, p_data in enumerate(raw_pose_mp):
                if len(p_data) >= 17:
                    kps = [[float(pt[0]), float(pt[1]), float(pt[2]), float(pt[3]), str(COCO_KEYPOINT_NAMES[i])] for i, pt in enumerate(p_data[:17])]
                    current_frame_people.append({'person_id': p_idx, 'keypoints': kps})
        else:
            raw_pose = get_pose_service().detect_pose_with_tracking(frame_resized, persist=True)
            tracked_persons = raw_pose.get('tracked_persons', [])
            
            for p_data in tracked_persons:
                pid = p_data['person_id']
                coords = p_data['keypoints']
                confs = p_data['confidences']
                
                kps = []
                for i in range(17):
                    x, y = coords[i] if i < len(coords) else (0.0, 0.0)
                    c = confs[i] if i < len(confs) else 0.0
                    kps.append([float(x), float(y), 0.0, float(c), str(COCO_KEYPOINT_NAMES[i])])
                
                if len(kps) >= 17:
                    current_frame_people.append({'person_id': pid, 'keypoints': kps})

        num_people = len(current_frame_people)
        
        # Analizar cada persona
        for p_data in current_frame_people:
            pid = p_data['person_id']
            kps = p_data['keypoints']
            
            # Dibujar esqueletos si estamos en modo analítico o debug (el front lo gestiona en LiveActionMultiPerson.tsx)
            if self.mode in ['analitico', 'debug']:
                self._draw_skeleton(output_frame, kps, frame.shape)
            
            # Inicializar estado para nueva persona
            if pid not in self.states_history:
                self.states_history[pid] = {
                    "state": "NEUTRAL",
                    "event_label": None,
                    "history": deque(maxlen=64),
                    "end_counter": 0,
                    "current_event": None
                }
            
            person_state = self.states_history[pid]
            if pid not in self.buffers:
                self.buffers[pid] = deque(maxlen=self.WINDOW_SIZE)
            
            self.buffers[pid].append([[kp[0], kp[1]] for kp in kps])

            # Si tenemos suficientes frames en el buffer, predecir
            if len(self.buffers[pid]) == self.WINDOW_SIZE:
                seq = np.array(self.buffers[pid], dtype=np.float32)
                try:
                    prediction = get_behavior_service().predict_behavior(seq, confidence_threshold=0.0)
                    pred_label = prediction.get('behavior', 'UNKNOWN')
                    prob = float(prediction.get('confidence', 0.0))
                    
                    person_state["history"].append((pred_label, prob))
                    historial_reciente = list(person_state["history"])[-self.EVAL_WINDOW:]

                    # En live mode usamos un threshold base moderado, ya que el usuario puede configurarlo desde UI (pero no se pasa aquí)
                    # Lo definiremos en 0.70 por defecto para que sea responsivo en vivo.
                    confidence_threshold_live = 0.70
                    pelear_frames = sum(1 for lbl, p in historial_reciente if lbl == "PELEAR" and p >= confidence_threshold_live)
                    disturbio_frames = sum(1 for lbl, p in historial_reciente if lbl == "DISTURBIO" and p >= confidence_threshold_live)
                    calma_frames = len(historial_reciente) - pelear_frames - disturbio_frames

                    sustained_action = person_state.get("event_label") or "NEUTRAL"

                    if sustained_action == "NEUTRAL":
                        if pelear_frames >= self.MIN_P: sustained_action = "PELEAR"
                        elif disturbio_frames >= self.MIN_D: sustained_action = "DISTURBIO"
                    elif sustained_action == "PELEAR":
                        if calma_frames >= self.END_W: sustained_action = "NEUTRAL"
                        elif disturbio_frames >= self.MIN_D: sustained_action = "DISTURBIO"
                    elif sustained_action == "DISTURBIO":
                        if calma_frames >= self.ESCAPE_D: sustained_action = "NEUTRAL"
                        elif pelear_frames >= self.MIN_P: sustained_action = "PELEAR"

                    if person_state["state"] == "NEUTRAL":
                        if sustained_action in ["PELEAR", "DISTURBIO"]:
                            person_state["state"] = "EVENTO"
                            person_state["event_label"] = sustained_action
                            
                            frames_prediccion = self.MIN_P if sustained_action == "PELEAR" else self.MIN_D
                            frames_esperados_reales = (frames_prediccion + self.WINDOW_SIZE) * self.frame_skip
                            inicio_real_frames = max(0, self.frame_counter - frames_esperados_reales)
                            
                            person_state["current_event"] = {
                                "tipo_evento": sustained_action,
                                "confianza": float(prob),
                                "frame_inicio": inicio_real_frames,
                                "segundo_inicio": float(inicio_real_frames / self.fps_estimate),
                                "personas_involucradas": 1,
                                "detalles": {'mode': self.mode, 'dimension': self.dimension, 'pid': pid}
                            }
                            
                            behaviors_detected.append(sustained_action)
                            self.realtime_unique_behaviors.add(sustained_action)
                            
                    else:
                        if sustained_action != person_state["event_label"]:
                            person_state["end_counter"] += 1
                            if person_state["end_counter"] >= self.END_W:
                                person_state["current_event"]["frame_fin"] = self.frame_counter
                                person_state["current_event"]["segundo_fin"] = current_time
                                self.all_detections.append(person_state["current_event"])
                                
                                person_state["state"] = "NEUTRAL"
                                person_state["event_label"] = None
                                person_state["current_event"] = None
                                person_state["end_counter"] = 0
                        else:
                            person_state["end_counter"] = 0
                            if prob > person_state["current_event"]["confianza"]:
                                person_state["current_event"]["confianza"] = float(prob)
                                
                            # Seguir reportando mientras dura
                            behaviors_detected.append(sustained_action)
                            self.realtime_unique_behaviors.add(sustained_action)

                except Exception as e:
                    print(f"Error LSTM Predict in LiveProcessor: {e}")
                    
            # Visualizar bounding box o indicador en vivo
            if self.mode != 'operativo':
                pos_x = np.mean([kp[0] for kp in kps]) if kps else 0.5
                pos_y = np.mean([kp[1] for kp in kps]) if kps else 0.5
                h, w, _ = frame.shape
                # Dibujar ID
                cv2.putText(output_frame, f"ID: {pid}", (int(pos_x * w), int(pos_y * h)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Dibujar info general
        cv2.putText(output_frame, f"Personas: {num_people}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Filtrar duplicados
        behaviors_detected = list(set(behaviors_detected))
        
        return output_frame, behaviors_detected, num_people

    def _draw_skeleton(self, frame, keypoints, shape):
        """Dibuja el esqueleto simple sobre el frame para visualización"""
        h, w, _ = shape
        for kp in keypoints:
            x, y, z, conf, name = kp
            if conf > 0.5:
                cv2.circle(frame, (int(x * w), int(y * h)), 3, (0, 255, 255), -1)

    def frame_to_base64(self, frame):
        """Codifica un frame BGR a base64 JPEG."""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return base64.b64encode(buffer).decode('utf-8')

    def get_all_detections(self):
        """Consolida y retorna todas las detecciones al finalizar."""
        # Cerrar eventos activos
        current_time = self.frame_counter / self.fps_estimate
        for p_id, state_info in self.states_history.items():
            if state_info["state"] == "EVENTO" and state_info["current_event"]:
                state_info["current_event"]["frame_fin"] = self.frame_counter
                state_info["current_event"]["segundo_fin"] = current_time
                self.all_detections.append(state_info["current_event"])

        if not self.all_detections:
            return []

        # Ordenar y consolidar (como en video_processor)
        self.all_detections.sort(key=lambda x: x['segundo_inicio'])
        consolidated = []
        
        curr_ev = self.all_detections[0].copy()
        for ev in self.all_detections[1:]:
            if ev['segundo_inicio'] <= curr_ev['segundo_fin'] + 2.0:
                curr_ev['segundo_fin'] = max(curr_ev['segundo_fin'], ev['segundo_fin'])
                curr_ev['frame_fin'] = max(curr_ev['frame_fin'], ev['frame_fin'])
                curr_ev['confianza'] = max(curr_ev['confianza'], ev['confianza'])
                curr_ev['personas_involucradas'] += 1
                if ev['tipo_evento'] == 'PELEAR' and curr_ev['tipo_evento'] != 'PELEAR':
                    curr_ev['tipo_evento'] = 'PELEAR'
            else:
                consolidated.append(curr_ev)
                curr_ev = ev.copy()
        consolidated.append(curr_ev)
        
        return consolidated

    def reset(self):
        """Reinicia el estado del procesador."""
        self.frame_counter = 0
        self.buffers = {}
        self.states_history = {}
        self.all_detections = []
        self.reporte_eventos = []
        self.realtime_unique_behaviors = set()
