"""
Módulo de inicialización de servicios
"""

from .pose_detection import PoseDetectionService
from .behavior_detection import BehaviorDetectionService
from .config_loader import SystemConfig

# Instancias globales de los servicios
pose_service = None
behavior_service = None

def initialize_services():
    """Inicializa los servicios de IA."""
    global pose_service, behavior_service
    
    try:
        pose_service = PoseDetectionService()
        print("✓ Servicio de detección de pose inicializado")
    except Exception as e:
        print(f"✗ Error inicializando servicio de pose: {e}")
    
    try:
        behavior_service = BehaviorDetectionService()
        print("✓ Servicio de detección de comportamiento inicializado")
    except Exception as e:
        print(f"✗ Error inicializando servicio de comportamiento: {e}")

def get_pose_service():
    """Retorna la instancia del servicio de pose."""
    global pose_service
    if pose_service is None:
        pose_service = PoseDetectionService()
    return pose_service

def get_behavior_service():
    """Retorna la instancia del servicio de comportamiento."""
    global behavior_service
    if behavior_service is None:
        behavior_service = BehaviorDetectionService()
    return behavior_service

def get_config():
    """Retorna la configuración del sistema."""
    return SystemConfig.to_dict()
