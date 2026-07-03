"""
Servicio de procesamiento en vivo de frames para detección de comportamientos sospechosos.
Migrado desde: BehaviorDetector (detectionMultipersonAction/Tesis/src/model/BehaviorDetector.py)

Detecta:
  - hidden_hands: manos ocultas detrás del cuerpo
  - excessive_gaze: giros bruscos / mirada excesiva 
  - hand_under_clothes: mano introducida bajo la ropa
"""

import cv2
import numpy as np
import math
import base64
import time
from collections import deque

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    print("⚠️ MediaPipe no está instalado. La detección en vivo de comportamientos individuales no estará disponible.")


class LiveProcessor:
    """
    Procesa un frame a la vez, manteniendo estado interno para detectar
    comportamientos sospechosos sostenidos en el tiempo.
    """

    def __init__(self, frame_skip=3, dimension='2D'):
        if not HAS_MEDIAPIPE:
            raise RuntimeError("MediaPipe es requerido para la detección en vivo.")

        self.frame_skip = max(1, int(frame_skip))
        self.dimension = dimension
        self.frame_counter = 0
        self.fps_estimate = 30.0  # Se actualiza con el timestamp real

        # ---- MediaPipe Models ----
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_face_mesh = mp.solutions.face_mesh

        # 2D = Modelo Ligero (0 o 1), 3D = Modelo Pesado (2) para mejor estimación de profundidad
        complexity = 2 if dimension == '3D' else 1

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=complexity,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # ---- Estado acumulado de la persona ----
        self.person_data = {
            'positions': deque(maxlen=30),
            'hidden_hands_frames': 0,
            'hidden_hands_duration': 0,
            'hidden_hands_position': None,
            'suspicious_start_times': {},
            'alerted': set(),
            'gaze_directions': deque(maxlen=60),
            'gaze_change_counter': 0,
            'last_significant_gaze_time': 0,
            'hand_under_clothes_frames': 0,
            'hand_under_clothes_duration': 0,
        }

        # ---- Umbrales ----
        self.hidden_hands_frame_threshold = max(1, 25 // self.frame_skip)
        self.hidden_hands_time_threshold = 3.0
        self.gaze_angle_threshold = 0.3
        self.gaze_changes_threshold = 8
        self.gaze_time_window = 5.0
        self.hand_under_clothes_frame_threshold = max(1, 20 // self.frame_skip)
        self.hand_under_clothes_time_threshold = 2.0
        self.arm_angle_threshold_min = 90
        self.arm_angle_threshold_max = 140
        self.confidence_threshold = 0.7

        # Indices de MediaPipe Face Mesh para ojos e iris
        self.LEFT_EYE_INDICES = [33, 133, 160, 159, 158, 144, 145, 153]
        self.RIGHT_EYE_INDICES = [362, 263, 386, 385, 384, 374, 373, 390]
        self.IRIS_INDICES = [468, 469, 470, 471, 472, 473]

        # ---- Detecciones acumuladas ----
        self.all_detections = []
        self.realtime_unique_behaviors = set()

    # =================================================================
    # Detectores individuales (migrados de BehaviorDetector.py)
    # =================================================================

    def detect_hand_pockets(self, pose_landmarks, multi_hands):
        """Detecta manos ocultas detrás del cuerpo o fuera de vista."""
        if not pose_landmarks:
            return False
            
        # Si MediaPipe Hands logró detectar claramente las manos (puntos amarillos),
        # significa que están a la vista de la cámara.
        visible_hands_count = len(multi_hands) if multi_hands else 0
        if visible_hands_count >= 2:
            return False # Ambas manos están visibles, no están ocultas
            
        l_wrist = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST]
        r_wrist = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        l_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP]
        r_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Opción 1: Las muñecas no son visibles (ocultas)
        if l_wrist.visibility < 0.2 and r_wrist.visibility < 0.2:
            return True
            
        # Opción 2: Muñecas detrás del cuerpo (Z mayor al de la cadera)
        if (l_wrist.z > l_hip.z + 0.05) or (r_wrist.z > r_hip.z + 0.05):
            return True
            
        # Opción 3: Muñecas muy cerca de las caderas o en el centro (bolsillos o cruzadas)
        mid_hip_x = (l_hip.x + r_hip.x) / 2
        mid_hip_y = (l_hip.y + r_hip.y) / 2
        
        l_dist = math.sqrt((l_wrist.x - l_hip.x)**2 + (l_wrist.y - l_hip.y)**2)
        r_dist = math.sqrt((r_wrist.x - r_hip.x)**2 + (r_wrist.y - r_hip.y)**2)
        center_l_dist = math.sqrt((l_wrist.x - mid_hip_x)**2 + (l_wrist.y - mid_hip_y)**2)
        center_r_dist = math.sqrt((r_wrist.x - mid_hip_x)**2 + (r_wrist.y - mid_hip_y)**2)
        
        # Solo aplicamos distancias si las muñecas tienen algo de visibilidad
        if l_wrist.visibility > 0.3 or r_wrist.visibility > 0.3:
            if l_dist < 0.25 or r_dist < 0.25 or center_l_dist < 0.2 or center_r_dist < 0.2:
                return True
            
        return False

    def detect_hand_under_clothes(self, pose_landmarks):
        """Detecta mano introducida bajo la ropa (ángulo del brazo + proximidad a cadera/pecho)."""
        if not pose_landmarks:
            return False

        left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        left_elbow = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ELBOW]
        left_wrist = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        right_elbow = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
        right_wrist = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]

        def calc_angle(shoulder, elbow, wrist):
            v1 = np.array([shoulder.x - elbow.x, shoulder.y - elbow.y])
            v2 = np.array([wrist.x - elbow.x, wrist.y - elbow.y])
            dot = np.dot(v1, v2)
            norms = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norms == 0:
                return 0
            return np.degrees(np.arccos(np.clip(dot / norms, -1.0, 1.0)))

        def near_torso(wrist, shoulder, threshold=0.3):
            # Cerca del pecho/torso
            return math.sqrt((wrist.x - shoulder.x) ** 2 + (wrist.y - shoulder.y) ** 2) < threshold

        left_angle = calc_angle(left_shoulder, left_elbow, left_wrist)
        right_angle = calc_angle(right_shoulder, right_elbow, right_wrist)

        # Hacemos los umbrales más flexibles
        suspicious_left = (45 <= left_angle <= 160) and near_torso(left_wrist, left_shoulder)
        suspicious_right = (45 <= right_angle <= 160) and near_torso(right_wrist, right_shoulder)

        return suspicious_left or suspicious_right

    def detect_excessive_gaze(self, face_landmarks, pose_landmarks, frame_shape, current_time):
        """Detecta giros bruscos y excesivos de la cabeza/mirada, y miradas fijas prolongadas."""
        if not face_landmarks and not pose_landmarks:
            return False

        gaze_vector = None

        if face_landmarks:
            left_eye_center = np.mean([[face_landmarks.landmark[idx].x, face_landmarks.landmark[idx].y]
                                        for idx in self.LEFT_EYE_INDICES], axis=0)
            right_eye_center = np.mean([[face_landmarks.landmark[idx].x, face_landmarks.landmark[idx].y]
                                         for idx in self.RIGHT_EYE_INDICES], axis=0)
            eyes_center = np.mean([left_eye_center, right_eye_center], axis=0)

            has_iris = len(face_landmarks.landmark) > 468
            if has_iris:
                left_iris = np.mean([[face_landmarks.landmark[idx].x, face_landmarks.landmark[idx].y]
                                      for idx in self.IRIS_INDICES[:3]], axis=0)
                right_iris = np.mean([[face_landmarks.landmark[idx].x, face_landmarks.landmark[idx].y]
                                       for idx in self.IRIS_INDICES[3:]], axis=0)
                gaze_vector = np.mean([left_iris - left_eye_center, right_iris - right_eye_center], axis=0)
            else:
                nose_tip = np.array([face_landmarks.landmark[4].x, face_landmarks.landmark[4].y])
                gaze_vector = nose_tip - eyes_center

        elif pose_landmarks:
            nose = np.array([pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE].x,
                             pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE].y])
            left_eye = np.array([pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EYE].x,
                                 pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EYE].y])
            right_eye = np.array([pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EYE].x,
                                  pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EYE].y])
            eyes_center = np.mean([left_eye, right_eye], axis=0)
            gaze_vector = nose - eyes_center

        if gaze_vector is None:
            return False

        mag = np.linalg.norm(gaze_vector)
        if mag > 0:
            gaze_vector = gaze_vector / mag
        else:
            return False

        self.person_data['gaze_directions'].append(gaze_vector)
        if len(self.person_data['gaze_directions']) < 2:
            return False

        prev_gaze = self.person_data['gaze_directions'][-2]
        dot = np.clip(np.dot(gaze_vector, prev_gaze), -1.0, 1.0)
        angle_change = np.arccos(dot)

        # Lógica 1: Mirada Fija (Staring) - Si el ángulo cambia muy poco
        if angle_change < 0.05:
            if 'staring_frames' not in self.person_data:
                self.person_data['staring_frames'] = 0
            self.person_data['staring_frames'] += self.frame_skip
            staring_duration = self.person_data['staring_frames'] / self.fps_estimate
            if staring_duration > 3.0: # 3 segundos mirando fijamente
                return True
        else:
            self.person_data['staring_frames'] = 0

        # Lógica 2: Giros Bruscos
        if angle_change > self.gaze_angle_threshold:
            self.person_data['gaze_change_counter'] += 1
            self.person_data['last_significant_gaze_time'] = current_time

            if 'excessive_gaze' not in self.person_data['suspicious_start_times']:
                self.person_data['suspicious_start_times']['excessive_gaze'] = current_time

        if 'excessive_gaze' in self.person_data['suspicious_start_times']:
            elapsed = current_time - self.person_data['suspicious_start_times']['excessive_gaze']
            if current_time - self.person_data['last_significant_gaze_time'] > self.gaze_time_window:
                self.person_data['gaze_change_counter'] = 0
                del self.person_data['suspicious_start_times']['excessive_gaze']
                self.person_data['alerted'].discard('excessive_gaze')
                return False
            if (self.person_data['gaze_change_counter'] >= self.gaze_changes_threshold and
                    elapsed <= self.gaze_time_window):
                return True

        return False

    # =================================================================
    # Procesamiento principal de un frame
    # =================================================================

    def process_frame(self, frame, overlay_only=False):
        """
        Procesa un frame BGR de OpenCV.
        Retorna: (output_frame_bgr, behaviors_list, num_people)
        """
        self.frame_counter += 1
        process_this = (self.frame_skip == 0) or (self.frame_counter % self.frame_skip == 0)

        if overlay_only:
            output_frame = np.zeros_like(frame)
        else:
            output_frame = frame.copy()
            
        behaviors_detected = []

        if not process_this:
            return output_frame, behaviors_detected, 0

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pose_results = self.pose.process(frame_rgb)

        num_people = 1 if pose_results.pose_landmarks else 0

        if pose_results.pose_landmarks:
            hand_results = self.hands.process(frame_rgb)
            face_results = self.face_mesh.process(frame_rgb)
            current_time = self.frame_counter / self.fps_estimate

            # Posición del torso para las etiquetas
            torso = [
                pose_results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER],
                pose_results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER],
                pose_results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP],
                pose_results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP]
            ]
            pos_x = sum(l.x for l in torso) / len(torso)
            pos_y = sum(l.y for l in torso) / len(torso)
            h, w, _ = frame.shape

            # --- 1. Manos ocultas ---
            multi_hands = hand_results.multi_hand_landmarks if hand_results.multi_hand_landmarks else []
            hands_hidden = self.detect_hand_pockets(pose_results.pose_landmarks, multi_hands)

            if hands_hidden:
                self.person_data['hidden_hands_frames'] += self.frame_skip
                self.person_data['hidden_hands_duration'] = self.person_data['hidden_hands_frames'] / self.fps_estimate
                if 'hidden_hands' not in self.person_data['suspicious_start_times']:
                    self.person_data['suspicious_start_times']['hidden_hands'] = current_time
                    self.person_data['hidden_hands_position'] = (pos_x, pos_y)

                if (self.person_data['hidden_hands_frames'] > self.hidden_hands_frame_threshold and
                        self.person_data['hidden_hands_duration'] >= self.hidden_hands_time_threshold):
                    behaviors_detected.append('hidden_hands')
                    if 'hidden_hands' not in self.person_data['alerted']:
                        self.person_data['alerted'].add('hidden_hands')
                    cv2.putText(output_frame, "Manos ocultas", (int(pos_x * w) - 60, int(pos_y * h) - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                self.person_data['hidden_hands_frames'] = 0
                self.person_data['hidden_hands_duration'] = 0
                self.person_data['suspicious_start_times'].pop('hidden_hands', None)
                self.person_data['alerted'].discard('hidden_hands')

            # --- 2. Mirada excesiva ---
            face_lm = face_results.multi_face_landmarks[0] if face_results.multi_face_landmarks else None
            excessive = self.detect_excessive_gaze(face_lm, pose_results.pose_landmarks, frame.shape, current_time)
            if excessive:
                behaviors_detected.append('excessive_gaze')
                if 'excessive_gaze' not in self.person_data['alerted']:
                    self.person_data['alerted'].add('excessive_gaze')
                cv2.putText(output_frame, "Mirada excesiva", (int(pos_x * w) - 60, int(pos_y * h) - 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # --- 3. Mano bajo ropa ---
            hand_clothes = self.detect_hand_under_clothes(pose_results.pose_landmarks)
            if hand_clothes:
                self.person_data['hand_under_clothes_frames'] += self.frame_skip
                self.person_data['hand_under_clothes_duration'] = self.person_data['hand_under_clothes_frames'] / self.fps_estimate
                if 'hand_under_clothes' not in self.person_data['suspicious_start_times']:
                    self.person_data['suspicious_start_times']['hand_under_clothes'] = current_time

                if (self.person_data['hand_under_clothes_frames'] > self.hand_under_clothes_frame_threshold and
                        self.person_data['hand_under_clothes_duration'] >= self.hand_under_clothes_time_threshold):
                    behaviors_detected.append('hand_under_clothes')
                    if 'hand_under_clothes' not in self.person_data['alerted']:
                        self.person_data['alerted'].add('hand_under_clothes')
                    cv2.putText(output_frame, "Mano bajo ropa", (int(pos_x * w) - 60, int(pos_y * h) - 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                self.person_data['hand_under_clothes_frames'] = 0
                self.person_data['hand_under_clothes_duration'] = 0
                self.person_data['suspicious_start_times'].pop('hand_under_clothes', None)
                self.person_data['alerted'].discard('hand_under_clothes')

            # --- Registrar detección ---
            if behaviors_detected:
                self.all_detections.append({
                    'timestamp': current_time,
                    'behaviors': list(behaviors_detected)
                })
                for b in behaviors_detected:
                    self.realtime_unique_behaviors.add(b)

            # --- Dibujar esqueleto (Estilos amigables) ---
            # Estilos personalizados para la postura (Puntos blancos, conexiones cian)
            pose_landmark_style = self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=3)
            pose_connection_style = self.mp_drawing.DrawingSpec(color=(255, 200, 0), thickness=2) # Cian en BGR
            
            self.mp_drawing.draw_landmarks(
                output_frame, 
                pose_results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=pose_landmark_style,
                connection_drawing_spec=pose_connection_style
            )

            # Estilos para las manos (Puntos amarillos, conexiones naranjas)
            hand_landmark_style = self.mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3)
            hand_connection_style = self.mp_drawing.DrawingSpec(color=(0, 165, 255), thickness=2)
            
            if hand_results.multi_hand_landmarks:
                for hand_lm in hand_results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        output_frame, 
                        hand_lm, 
                        self.mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=hand_landmark_style,
                        connection_drawing_spec=hand_connection_style
                    )

            # NOTA: Omitimos dibujar la malla facial (FaceMesh) porque satura la imagen
            # de líneas blancas y resulta confuso, aunque la IA la sigue usando internamente.

        cv2.putText(output_frame, f"Personas: {num_people}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return output_frame, behaviors_detected, num_people

    def frame_to_base64(self, frame):
        """Codifica un frame BGR a base64 JPEG."""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return base64.b64encode(buffer).decode('utf-8')

    def get_all_detections(self):
        """Retorna todas las detecciones acumuladas."""
        return self.all_detections

    def reset(self):
        """Reinicia el estado del procesador."""
        self.frame_counter = 0
        self.all_detections = []
        self.realtime_unique_behaviors = set()
        self.person_data = {
            'positions': deque(maxlen=30),
            'hidden_hands_frames': 0,
            'hidden_hands_duration': 0,
            'hidden_hands_position': None,
            'suspicious_start_times': {},
            'alerted': set(),
            'gaze_directions': deque(maxlen=60),
            'gaze_change_counter': 0,
            'last_significant_gaze_time': 0,
            'hand_under_clothes_frames': 0,
            'hand_under_clothes_duration': 0,
        }
