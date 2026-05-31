# Capa de Servicios de IA y Procesamiento de Video
# Esta carpeta contiene la lógica reutilizable del sistema anterior

Este módulo encapsula toda la lógica de detección de pose y análisis de comportamiento
que será compartida entre Django, Celery workers y cualquier otro consumidor.

## Estructura

- `pose_detection.py` - Detección de puntos clave (keypoints) usando YOLO
- `behavior_detection.py` - Detección de comportamientos usando LSTM
- `video_processor.py` - Procesamiento de videos y streams
- `config_loader.py` - Carga de parámetros del sistema
- `resources/` - Módulos reutilizables del Tesis (Conexion, Encrypt, etc)
- `models/` - Modelos preentrenados (YOLO, LSTM)
