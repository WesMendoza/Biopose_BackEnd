"""
Servicio de Detección de Pose
Encapsula la lógica de detección de puntos clave usando YOLO.
"""

import os
from ultralytics import YOLO
import cv2
import numpy as np

class PoseDetectionService:
    def __init__(self, model_path=None):
        """
        Inicializa el servicio de detección de pose.
        
        Args:
            model_path: Ruta al modelo YOLO. Si es None, usa la ruta por defecto.
        """
        if model_path is None:
            model_path = os.getenv('YOLO_MODEL_PATH', 'yolov8s-pose.pt')
        
        self.model = YOLO(model_path)
        self.device = 'cpu'  # Cambiar a 'cuda' si hay GPU disponible
        self.model.to(self.device)
    
    def detect_pose_image(self, image_path):
        """
        Detecta pose en una imagen.
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            dict con resultados (keypoints, confidencia, etc)
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")
        
        results = self.model(image)
        return self._parse_results(results)
    
    def detect_pose_frame(self, frame):
        """
        Detecta pose en un frame de video.
        
        Args:
            frame: Frame de OpenCV (numpy array)
            
        Returns:
            dict con resultados
        """
        results = self.model(frame, verbose=False)
        return self._parse_results(results)

    def detect_and_draw_pose_frame(self, frame):
        """
        Detecta pose en un frame y dibuja los keypoints.
        
        Args:
            frame: Frame de OpenCV (numpy array)
            
        Returns:
            tuple: (dict con resultados, numpy array con imagen anotada)
        """
        results = self.model(frame, verbose=False)
        parsed = self._parse_results(results)
        
        annotated_frame = frame
        if results and len(results) > 0:
            annotated_frame = results[0].plot()
            
        return parsed, annotated_frame
    
    def detect_pose_with_tracking(self, frame, persist=True):
        """
        Detecta pose con seguimiento de personas (tracking).
        
        Args:
            frame: Frame de OpenCV
            persist: Mantener IDs entre frames
            
        Returns:
            dict con keypoints y IDs de personas
        """
        results = self.model.track(frame, persist=persist, verbose=False, tracker='bytetrack.yaml')
        return self._parse_tracking_results(results)
    
    def _parse_results(self, results):
        """Convierte resultados de YOLO a formato estándar."""
        if results is None or len(results) == 0:
            return {'keypoints': [], 'confidences': []}
        
        result = results[0]
        kps = result.keypoints
        
        if kps is None or kps.xy is None:
            return {'keypoints': [], 'confidences': []}
        
        keypoints_list = []
        kps_xy = kps.xy.cpu().numpy()
        
        for person_idx, person_kps in enumerate(kps_xy):
            keypoints_list.append({
                'person_id': person_idx,
                'keypoints': person_kps.tolist()
            })
        
        return {
            'keypoints': keypoints_list,
            'confidences': kps.conf.cpu().numpy().tolist() if hasattr(kps, 'conf') else []
        }
    
    def _parse_tracking_results(self, results):
        """Convierte resultados de tracking a formato estándar."""
        if results is None or len(results) == 0 or results[0].keypoints is None:
            return {'tracked_persons': []}
        
        result = results[0]
        tracked_persons = []
        
        kps = result.keypoints
        boxes = result.boxes
        
        if boxes.id is None:
            return {'tracked_persons': []}
        
        for person_id, keypoints, box in zip(boxes.id.cpu().numpy(), 
                                            kps.xy.cpu().numpy(),
                                            boxes.xyxy.cpu().numpy()):
            tracked_persons.append({
                'person_id': int(person_id),
                'keypoints': keypoints.tolist(),
                'bbox': box.tolist()
            })
        
        return {'tracked_persons': tracked_persons}
