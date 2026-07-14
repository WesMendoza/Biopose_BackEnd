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
        self.MIN_P = 3
        self.MIN_D = 3
        self.END_W = 5
        self.ESCAPE_D = 5

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
            
            # --- Reparación de Tracker (Tracker Repair) ---
            # En modo 2D (YOLOv8), el rastreador (ByteTrack) suele perder el ID de la persona cuando hay saltos de frames 
            # rápidos o movimientos bruscos. Si el ID cambia, el buffer LSTM se vacía y se pierde la acción (como un golpe).
            # Para evitar esto, reasignamos los buffers de los IDs perdidos a los IDs nuevos si sus narices están cerca.
            current_noses = {p['person_id']: p['keypoints'][0] for p in tracked_persons if len(p['keypoints']) > 0}
            new_pids = [pid for pid in current_noses.keys() if pid not in self.buffers]
            missing_pids = [pid for pid in self.buffers.keys() if pid not in current_noses.keys()]
            
            if new_pids and missing_pids:
                for new_pid in new_pids:
                    new_nose = current_noses[new_pid]
                    best_old_pid = None
                    min_dist = 200.0  # Tolerancia máxima de 200 píxeles
                    
                    for old_pid in missing_pids:
                        if len(self.buffers[old_pid]) > 0:
                            old_nose = self.buffers[old_pid][-1][0] # kp[0] es la nariz en el buffer
                            dist = ((new_nose[0] - old_nose[0])**2 + (new_nose[1] - old_nose[1])**2)**0.5
                            if dist < min_dist:
                                min_dist = dist
                                best_old_pid = old_pid
                    
                    if best_old_pid is not None:
                        # Transferir la memoria LSTM (buffer) al nuevo ID para no interrumpir el análisis
                        self.buffers[new_pid] = self.buffers.pop(best_old_pid)
                        if best_old_pid in self.states_history:
                            self.states_history[new_pid] = self.states_history.pop(best_old_pid)
                        missing_pids.remove(best_old_pid)
            # ----------------------------------------------
            
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
            
            current_kps = [[kp[0], kp[1]] for kp in kps]
            
            # Aplicar suavizado temporal (EMA) para reducir el 'jitter' de YOLOv8 en modo 2D.
            # Esto ayuda enormemente a la red LSTM a calcular velocidades limpias.
            if len(self.buffers[pid]) > 0 and not self.usar_3d:
                prev_kps = self.buffers[pid][-1]
                alpha = 0.85  # 0.85 suaviza el ruido micrométrico pero mantiene la velocidad de los puños
                smoothed_kps = []
                for i in range(len(current_kps)):
                    sx = alpha * current_kps[i][0] + (1 - alpha) * prev_kps[i][0]
                    sy = alpha * current_kps[i][1] + (1 - alpha) * prev_kps[i][1]
                    smoothed_kps.append([sx, sy])
                self.buffers[pid].append(smoothed_kps)
            else:
                self.buffers[pid].append(current_kps)

            # Si tenemos suficientes frames en el buffer, predecir
            if len(self.buffers[pid]) == self.WINDOW_SIZE:
                seq = np.array(self.buffers[pid], dtype=np.float32)
                try:
                    prediction = get_behavior_service().predict_behavior(seq, confidence_threshold=0.0)
                    pred_label = prediction.get('behavior', 'UNKNOWN')
                    prob = float(prediction.get('confidence', 0.0))
                    
                    person_state["history"].append((pred_label, prob))
                    historial_reciente = list(person_state["history"])[-self.EVAL_WINDOW:]

                    # Ajuste dinámico de sensibilidad: YOLOv8 (2D) genera datos distintos al dataset original
                    # bajando la confianza de la red. Lo compensamos relajando el umbral exclusivamente para 2D.
                    confidence_threshold_live = 0.50 if self.usar_3d else 0.35
                    min_frames = self.MIN_P if self.usar_3d else 2
                    
                    pelear_frames = sum(1 for lbl, p in historial_reciente if lbl == "PELEAR" and p >= confidence_threshold_live)
                    disturbio_frames = sum(1 for lbl, p in historial_reciente if lbl == "DISTURBIO" and p >= confidence_threshold_live)
                    calma_frames = len(historial_reciente) - pelear_frames - disturbio_frames

                    sustained_action = person_state.get("event_label") or "NEUTRAL"

                    if sustained_action == "NEUTRAL":
                        if pelear_frames >= min_frames: sustained_action = "PELEAR"
                        elif disturbio_frames >= min_frames: sustained_action = "DISTURBIO"
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
                    
            # Visualizar bounding box de la persona basado en su estado de comportamiento
            h, w, _ = frame.shape
            if kps:
                valid_kps = [kp for kp in kps if kp[3] > 0.1] # Puntos con algo de confianza
                if valid_kps:
<<<<<<< HEAD
                    min_x = max(0, int(min([kp[0] for kp in valid_kps])) - 20)
                    min_y = max(0, int(min([kp[1] for kp in valid_kps])) - 20)
                    max_x = min(w, int(max([kp[0] for kp in valid_kps])) + 20)
                    max_y = min(h, int(max([kp[1] for kp in valid_kps])) + 20)
=======
                    # Escalar las coordenadas del modelo (640x640) al tamaño original del frame
                    scale_x = w / 640.0
                    scale_y = h / 640.0
                    
                    min_x = max(0, int(min([kp[0] for kp in valid_kps]) * scale_x) - 20)
                    min_y = max(0, int(min([kp[1] for kp in valid_kps]) * scale_y) - 20)
                    max_x = min(w, int(max([kp[0] for kp in valid_kps]) * scale_x) + 20)
                    max_y = min(h, int(max([kp[1] for kp in valid_kps]) * scale_y) + 20)
>>>>>>> ef0d37b6b1c6ca81384eebc67f21a5d5d3902688

                    # Determinar color según el evento
                    estado_actual = person_state.get("event_label") or "NEUTRAL"
                    if estado_actual == "PELEAR":
                        color = (0, 0, 255) # Rojo en BGR
                        label_text = f"[{pid}] PELEA"
                    elif estado_actual == "DISTURBIO":
                        color = (0, 165, 255) # Naranja en BGR
                        label_text = f"[{pid}] DISTURBIO"
                    else:
                        color = (0, 255, 0) # Verde en BGR
                        label_text = f"[{pid}] NORMAL"
                    
                    # Dibujar Rectángulo del cuerpo
                    cv2.rectangle(output_frame, (min_x, min_y), (max_x, max_y), color, 2)
                    
                    # Dibujar etiqueta de texto sobre el rectángulo
                    (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(output_frame, (min_x, min_y - 20), (min_x + text_w, min_y), color, -1)
                    cv2.putText(output_frame, label_text, (min_x, min_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255) if estado_actual == "PELEAR" else (0,0,0), 1)

        # Dibujar info general
        cv2.putText(output_frame, f"Personas: {num_people}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Filtrar duplicados
        behaviors_detected = list(set(behaviors_detected))
        
        return output_frame, behaviors_detected, num_people

    def _draw_skeleton(self, frame, keypoints, shape):
        """Dibuja el esqueleto simple sobre el frame para visualización"""
        h, w, _ = shape
        scale_x = w / 640.0
        scale_y = h / 640.0
        for kp in keypoints:
            x, y, z, conf, name = kp
            if conf > 0.5:
<<<<<<< HEAD
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 255), -1)
=======
                cv2.circle(frame, (int(x * scale_x), int(y * scale_y)), 3, (0, 255, 255), -1)
>>>>>>> ef0d37b6b1c6ca81384eebc67f21a5d5d3902688

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
