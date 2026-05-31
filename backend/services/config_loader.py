"""
Configuración centralizada de parámetros del sistema.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class SystemConfig:
    """Clase que centraliza la configuración del sistema."""
    
    # Parámetros de YOLO
    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'yolov8s-pose.pt')
    YOLO_DEVICE = os.getenv('YOLO_DEVICE', 'cpu')
    YOLO_CONF_THRESHOLD = float(os.getenv('YOLO_CONF_THRESHOLD', '0.5'))
    
    # Parámetros de LSTM
    LSTM_MODEL_PATH = os.getenv('LSTM_MODEL_PATH', 'models/lstm_3clasesstride1.pt')
    LABEL_MAP_PATH = os.getenv('LABEL_MAP_PATH', 'models/label_map_3clases.json')
    LSTM_WINDOW_SIZE = int(os.getenv('LSTM_WINDOW_SIZE', '32'))
    
    # Thresholds de detección
    THRESHOLD_PELEA = float(os.getenv('THRESHOLD_PELEA', '0.75'))
    THRESHOLD_DISTURBIO = float(os.getenv('THRESHOLD_DISTURBIO', '0.92'))
    MIN_EVENT_PELEA = int(os.getenv('MIN_EVENT_PELEA', '25'))
    MIN_EVENT_DISTURBIO = int(os.getenv('MIN_EVENT_DISTURBIO', '60'))
    END_EVENT_WINDOWS = int(os.getenv('END_EVENT_WINDOWS', '20'))
    
    # Rutas de procesamiento
    VIDEOS_UPLOAD_DIR = os.getenv('VIDEOS_UPLOAD_DIR', 'media/videos/uploads')
    VIDEOS_RESULTS_DIR = os.getenv('VIDEOS_RESULTS_DIR', 'media/videos/results')
    PROCESSED_VIDEOS_DIR = os.getenv('PROCESSED_VIDEOS_DIR', 'media/videos/processed')
    
    # Parámetros de procesamiento
    MAX_VIDEO_SIZE_MB = int(os.getenv('MAX_VIDEO_SIZE_MB', '500'))
    FRAME_SKIP = int(os.getenv('FRAME_SKIP', '1'))
    FPS_OUTPUT = int(os.getenv('FPS_OUTPUT', '30'))
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Base de datos
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'Dev')
    
    @classmethod
    def validate_paths(cls):
        """Valida que las rutas de configuración existan."""
        for attr in ['VIDEOS_UPLOAD_DIR', 'VIDEOS_RESULTS_DIR', 'PROCESSED_VIDEOS_DIR']:
            path = getattr(cls, attr)
            os.makedirs(path, exist_ok=True)
    
    @classmethod
    def to_dict(cls):
        """Convierte la configuración a un diccionario."""
        return {key: getattr(cls, key) for key in dir(cls) 
                if not key.startswith('_') and key.isupper()}


# Validar rutas al importar
SystemConfig.validate_paths()
