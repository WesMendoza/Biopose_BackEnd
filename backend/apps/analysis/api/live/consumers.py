"""
Consumer WebSocket para detección en vivo desde la cámara del cliente.
El navegador envía frames base64 por WebSocket, el backend los procesa
con LiveProcessor y devuelve los resultados (detecciones + keypoints).
"""

import json
import base64
import numpy as np
import cv2
from channels.generic.websocket import WebsocketConsumer

from services.live_processor import LiveProcessor


class LiveDetectionConsumer(WebsocketConsumer):
    """
    WebSocket síncrono para procesamiento de frames enviados desde el navegador.
    """

    def connect(self):
        self.processor = None
        self.accept()
        self.send(text_data=json.dumps({'status': 'connected'}))

    def disconnect(self, close_code):
        if self.processor:
            # Enviar detecciones finales antes de cerrar
            final = self.processor.get_all_detections()
            try:
                self.send(text_data=json.dumps({
                    'type': 'final',
                    'detections': final
                }))
            except Exception:
                pass
            self.processor = None

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            frame_b64 = data.get('frame', '')
            fps_skip = int(data.get('fps_skip', 3))
            dimension = data.get('mode', '2D')

            # Inicializar el procesador en el primer frame
            if self.processor is None:
                # El frontend ya realiza el salto de frames y nos envía solo los que debemos procesar.
                # Por tanto, aquí no saltamos ninguno (frame_skip=1).
                self.processor = LiveProcessor(frame_skip=1, dimension=dimension)
                # Estimamos los FPS reales que nos están llegando para que el cálculo de tiempo sea exacto.
                # Si el frontend salta 3 frames (de 30), nos llegan 10 FPS.
                self.processor.fps_estimate = 30.0 / (fps_skip if fps_skip > 0 else 1)

            # Decodificar el frame base64 a imagen BGR
            img_bytes = base64.b64decode(frame_b64)
            np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                self.send(text_data=json.dumps({'error': 'Frame inválido'}))
                return

            # Procesar el frame (pedimos solo overlay porque el frontend muestra el video local)
            output_frame, detections, num_people = self.processor.process_frame(frame, overlay_only=True)

            # Enviar la respuesta de vuelta al cliente
            response = {
                'type': 'result',
                'frame': self.processor.frame_to_base64(output_frame),
                'detections': detections if detections else [],
                'num_people': num_people,
                'realtime_behaviors': list(self.processor.realtime_unique_behaviors),
                'total_detections': len(self.processor.all_detections),
            }

            self.send(text_data=json.dumps(response))

        except Exception as e:
            self.send(text_data=json.dumps({'error': str(e)}))
