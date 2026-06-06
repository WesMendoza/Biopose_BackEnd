from django.urls import path, include

urlpatterns = [
    # Módulo de Manejo de Archivos/Media (Carga, renderización inicial)
    path('media/', include('apps.analysis.api.media.urls')),
    
    # -------------------------------------------------------------
    # Se descomentarán conforme avancemos en las iteraciones:
    # -------------------------------------------------------------
    # Módulo YOLO (Detección de Keypoints)
    path('pose/', include('apps.analysis.api.pose.urls')),
    
    # Módulo LSTM (Detección de comportamiento)
    path('videos/', include('apps.analysis.api.behavior.urls')),
    
    # Módulo Streaming (Websockets y monitoreo real-time)
    # path('', include('apps.analysis.api.live.urls')),
]
