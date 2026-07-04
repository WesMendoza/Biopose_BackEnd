import cv2
import mediapipe as mp

# Mapeo: Índice de COCO (YOLO) -> Índice equivalente en MediaPipe
MP_TO_COCO_MAPPING = {
    0: 0,   # Nariz
    1: 2,   # Ojo Izq
    2: 5,   # Ojo Der
    3: 7,   # Oreja Izq
    4: 8,   # Oreja Der
    5: 11,  # Hombro Izq
    6: 12,  # Hombro Der
    7: 13,  # Codo Izq
    8: 14,  # Codo Der
    9: 15,  # Muñeca Izq
    10: 16, # Muñeca Der
    11: 23, # Cadera Izq
    12: 24, # Cadera Der
    13: 25, # Rodilla Izq
    14: 26, # Rodilla Der
    15: 27, # Tobillo Izq
    16: 28  # Tobillo Der
}

class MediaPipePoseService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1, # 1 es buen balance entre velocidad y precisión (como YOLOv8s)
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def detect_pose_frame_3d(self, frame):
        """
        Procesa el frame con MediaPipe y lo devuelve en el formato 
        estandarizado de 17 puntos (COCO) pero con coordenada Z real.
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        
        # Estructura idéntica a la salida formateada de YOLO, para no romper el resto del sistema
        formatted_person = []
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, c = frame.shape
            
            for coco_idx in range(17):
                mp_idx = MP_TO_COCO_MAPPING.get(coco_idx)
                if mp_idx is not None:
                    lm = landmarks[mp_idx]
                    # MediaPipe da coordenadas normalizadas (0 a 1). Las pasamos a píxeles.
                    x = lm.x * w
                    y = lm.y * h
                    # La Z en MediaPipe está escalada proporcionalmente al ancho de los hombros.
                    # La multiplicamos por el ancho de la imagen para tener una escala útil.
                    z = lm.z * w 
                    conf = lm.visibility # Usamos la visibilidad como "confianza"
                    
                    formatted_person.append([x, y, z, conf])
                else:
                    formatted_person.append([0.0, 0.0, 0.0, 0.0])
                    
            return [formatted_person] # Retorna array de personas (aunque MP solo detecta 1 por ahora)
        
        return []