"""
Vistas para detección en vivo — Endpoint SSE (Server-Sent Events).
Permite al frontend recibir frames procesados en tiempo real desde una cámara
del servidor o conexión RTSP remota.
"""

import json
import cv2
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from services.live_processor import LiveProcessor
from services.live_action_multiperson_processor import LiveActionMultiPersonProcessor


def _generate_stream(source, fps_skip, dimension):
    """
    Generador que abre la fuente de video (cámara local o URL remota),
    procesa cada frame con LiveProcessor, y emite SSE.
    """
    processor = LiveProcessor(frame_skip=fps_skip, dimension=dimension)

    # source puede ser 0 (webcam local) o una URL string
    if isinstance(source, str) and (source.startswith('http') or source.startswith('rtsp')):
        # Quitar cv2.CAP_FFMPEG forzado porque puede fallar en Windows sin los binarios de FFmpeg
        cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        yield f"data: {json.dumps({'error': 'No se pudo abrir la fuente de video'})}\n\n"
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps and fps > 0:
        processor.fps_estimate = fps

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            output_frame, detections, num_people = processor.process_frame(frame)
            frame_b64 = processor.frame_to_base64(output_frame)

            payload = {
                'frame': frame_b64,
                'detections': detections if detections else None,
                'num_people': num_people,
            }
            yield f"data: {json.dumps(payload)}\n\n"

    except GeneratorExit:
        pass
    finally:
        cap.release()
        # Enviar las detecciones finales y señal de EOF
        final_detections = processor.get_all_detections()
        yield f"data: {json.dumps({'final_detections': final_detections})}\n\n"
        yield "data: EOF\n\n"


@csrf_exempt
def live_stream_sse(request):
    """
    GET /api/analysis/live/stream/?fps_skip=3&dimension=2D&source=local&url=rtsp://...
    
    Inicia un stream SSE que procesa la cámara del servidor o una fuente remota.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    fps_skip = int(request.GET.get('fps_skip', 3))
    dimension = request.GET.get('dimension', '2D')
    source_type = request.GET.get('source', 'local')
    remote_url = request.GET.get('url', '')

    # Determinar fuente de video
    if source_type == 'remote' and remote_url:
        source = remote_url
    else:
        source = 0  # Webcam local del servidor

    response = StreamingHttpResponse(
        _generate_stream(source, fps_skip, dimension),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@csrf_exempt
def live_detections(request):
    """
    GET /api/analysis/live/detections/
    Placeholder: en el flujo SSE, las detecciones finales se envían dentro del stream.
    """
    return JsonResponse({'detections': []})

def _generate_stream_multiperson(source, fps_skip, dimension, mode):
    processor = LiveActionMultiPersonProcessor(frame_skip=fps_skip, mode=mode, dimension=dimension)

    if isinstance(source, str) and (source.startswith('http') or source.startswith('rtsp')):
        cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        yield f"data: {json.dumps({'error': 'No se pudo abrir la fuente de video'})}\n\n"
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps and fps > 0:
        processor.fps_estimate = fps

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            output_frame, detections, num_people = processor.process_frame(frame)
            frame_b64 = processor.frame_to_base64(output_frame)

            payload = {
                'frame': frame_b64,
                'detections': detections if detections else None,
                'num_people': num_people,
            }
            yield f"data: {json.dumps(payload)}\n\n"

    except GeneratorExit:
        pass
    finally:
        cap.release()
        final_detections = processor.get_all_detections()
        yield f"data: {json.dumps({'final_detections': final_detections})}\n\n"
        yield "data: EOF\n\n"

@csrf_exempt
def live_action_multiperson_stream_sse(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    fps_skip = int(request.GET.get('fps_skip', 3))
    dimension = request.GET.get('dimension', '2D')
    source_type = request.GET.get('source', 'local')
    remote_url = request.GET.get('url', '')
    mode = request.GET.get('mode', 'operativo')
    
    # Adaptar modo
    if 'Analítico' in mode: mode = 'analitico'
    elif 'Debug' in mode: mode = 'debug'
    else: mode = 'operativo'

    if source_type == 'remote' and remote_url:
        source = remote_url
    else:
        source = 0 

    response = StreamingHttpResponse(
        _generate_stream_multiperson(source, fps_skip, dimension, mode),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
