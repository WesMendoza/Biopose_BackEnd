"""
VIEWS - Fase 3: Endpoints REST Básicos
======================================

Implementación funcional de los ViewSets para imágenes, videos y frames.
"""

import json
import os
import time
import uuid
import shutil
from datetime import datetime

import cv2
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, StreamingHttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from services.behavior_detection import BehaviorDetectionService
from services.pose_detection import PoseDetectionService
from services.video_processor import analyze_video_behavior, generate_frames_from_video

from .models import AnalysisReport, DetectionEvent, PersonKeypoints, VideoUpload
from .serializers import (
    AnalysisReportSerializer,
    DetectionEventSerializer,
    FrameDataSerializer,
    GenerateFramesRequestSerializer,
    GenerateFramesResponseSerializer,
    ImageProcessingResponseSerializer,
    ImageResizeSerializer,
    ImageSaveSerializer,
    ImageUploadSerializer,
    KeypointSerializer,
    PersonKeypointsSerializer,
    SSECompletedEventSerializer,
    SSEDetectionEventSerializer,
    SSEProgressEventSerializer,
    VideoProcessingRequestSerializer,
    VideoProcessingResponseSerializer,
    VideoResultsSerializer,
    VideoUploadFormSerializer,
    VideoUploadSerializer,
)


COCO_KEYPOINT_NAMES = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
]

COCO_SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
]

_POSE_SERVICE = None
_BEHAVIOR_SERVICE = None


def _project_root():
    return os.fspath(settings.BASE_DIR)


def _pose_service():
    global _POSE_SERVICE
    if _POSE_SERVICE is None:
        model_path = os.path.join(_project_root(), 'yolov8s-pose.pt')
        _POSE_SERVICE = PoseDetectionService(model_path=model_path)
    return _POSE_SERVICE


def _behavior_service():
    global _BEHAVIOR_SERVICE
    if _BEHAVIOR_SERVICE is None:
        model_path = os.path.join(_project_root(), 'resources', 'models', 'lstm_3clasesstride1.pt')
        label_map_path = os.path.join(_project_root(), 'resources', 'models', 'label_map_3clases.json')
        _BEHAVIOR_SERVICE = BehaviorDetectionService(model_path=model_path, label_map_path=label_map_path)
    return _BEHAVIOR_SERVICE


def _media_abs_path(*parts):
    return os.path.join(os.fspath(settings.MEDIA_ROOT), *parts)


def _media_rel_path(*parts):
    return os.path.join(*parts).replace('\\', '/')


def _timestamp_token():
    return datetime.now().strftime('%Y%m%d_%H%M%S_%f')


def _ensure_parent_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _position_from_dimensions(width, height):
    if width == height:
        return 'cuadrada'
    return 'horizontal' if width > height else 'vertical'


def _extract_keypoints_from_pose(raw_pose_data):
    persons = raw_pose_data.get('keypoints', []) if raw_pose_data else []
    confidences = raw_pose_data.get('confidences', []) if raw_pose_data else []
    if not persons:
        return []

    first_person = persons[0].get('keypoints', [])
    confidence_values = confidences[0] if confidences else []
    keypoints = []
    for index, name in enumerate(COCO_KEYPOINT_NAMES):
        point = first_person[index] if index < len(first_person) else [0.0, 0.0]
        confidence = float(confidence_values[index]) if index < len(confidence_values) else 0.0
        keypoints.append({
            'id': index,
            'name': name,
            'x': float(point[0]),
            'y': float(point[1]),
            'z': 0.0,
            'confidence': confidence,
        })
    return keypoints


def _draw_keypoints(image, keypoints):
    for keypoint in keypoints:
        x = int(round(keypoint['x']))
        y = int(round(keypoint['y']))
        cv2.circle(image, (x, y), 4, (0, 255, 0), -1)
        cv2.putText(image, str(keypoint['id']), (x + 3, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    for start_idx, end_idx in COCO_SKELETON:
        if start_idx < len(keypoints) and end_idx < len(keypoints):
            start_point = (int(round(keypoints[start_idx]['x'])), int(round(keypoints[start_idx]['y'])))
            end_point = (int(round(keypoints[end_idx]['x'])), int(round(keypoints[end_idx]['y'])))
            cv2.line(image, start_point, end_point, (255, 0, 0), 2)

    return image


def _relative_media_path(subfolder, filename):
    return _media_rel_path('media', subfolder, filename)


class ImageAnalysisViewSet(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        start_time = time.time()
        token = _timestamp_token()
        ext = os.path.splitext(image_file.name)[1].lower() or '.jpg'
        upload_filename = f'image_{token}{ext}'
        upload_relative_path = default_storage.save(os.path.join('images', 'uploads', upload_filename), image_file)
        upload_absolute_path = _media_abs_path(upload_relative_path)
        print('DEBUG upload_relative_path=', upload_relative_path)
        print('DEBUG upload_absolute_path=', upload_absolute_path)

        image = cv2.imread(upload_absolute_path)
        if image is None:
            return Response({'error': 'Processing failed', 'message': 'No se pudo leer la imagen cargada.'}, status=status.HTTP_400_BAD_REQUEST)

        original_height, original_width = image.shape[:2]
        try:
            pose_data = _pose_service().detect_pose_image(upload_absolute_path)
        except Exception as exc:
            return Response({'error': 'Processing failed', 'message': f'Error al procesar imagen: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        keypoints = _extract_keypoints_from_pose(pose_data)
        processed_image = _draw_keypoints(image.copy(), keypoints)
        processed_filename = f'image_keypoints_{token}.jpg'
        processed_absolute_path = _media_abs_path('images', 'processed', processed_filename)
        _ensure_parent_dir(processed_absolute_path)
        cv2.imwrite(processed_absolute_path, processed_image)

        response_data = {
            'id': int(time.time() * 1000) % 2147483647,
            'message': 'Imagen procesada exitosamente',
            'filename': processed_filename,
            'path': _relative_media_path('images', 'processed', processed_filename),
            'image_position': _position_from_dimensions(original_width, original_height),
            'keypoints': keypoints,
            'image_dimensions': {
                'original_width': original_width,
                'original_height': original_height,
                'processed_width': int(processed_image.shape[1]),
                'processed_height': int(processed_image.shape[0]),
            },
            'processing_time_ms': int((time.time() - start_time) * 1000),
            'model': 'yolov8s-pose',
        }
        return Response(ImageProcessingResponseSerializer(response_data).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def resize(self, request):
        serializer = ImageResizeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        width = serializer.validated_data['width']
        height = serializer.validated_data['height']
        if width <= 0 or height <= 0:
            return Response({'error': 'Invalid parameters', 'message': 'width y height deben ser números positivos.'}, status=status.HTTP_400_BAD_REQUEST)

        token = _timestamp_token()
        ext = os.path.splitext(image_file.name)[1].lower() or '.jpg'
        upload_relative_path = default_storage.save(os.path.join('images', 'uploads', f'resize_{token}{ext}'), image_file)
        upload_absolute_path = _media_abs_path(upload_relative_path)

        image = cv2.imread(upload_absolute_path)
        if image is None:
            return Response({'error': 'Processing failed', 'message': 'No se pudo leer la imagen cargada.'}, status=status.HTTP_400_BAD_REQUEST)

        original_height, original_width = image.shape[:2]
        resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        resized_filename = f'image_resized_{token}.jpg'
        resized_absolute_path = _media_abs_path('images', 'processed', resized_filename)
        _ensure_parent_dir(resized_absolute_path)
        cv2.imwrite(resized_absolute_path, resized_image)

        response_data = {
            'message': 'Imagen redimensionada exitosamente.',
            'filename': resized_filename,
            'path': _relative_media_path('images', 'processed', resized_filename),
            'new_dimensions': {'width': width, 'height': height},
            'original_dimensions': {'width': original_width, 'height': original_height},
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def save(self, request):
        serializer = ImageSaveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data
        image_id = payload['image_id']
        token = _timestamp_token()
        storage_filename = f'image_{image_id}_{token}.json'
        storage_absolute_path = _media_abs_path('images', 'processed', storage_filename)
        _ensure_parent_dir(storage_absolute_path)

        with open(storage_absolute_path, 'w', encoding='utf-8') as handle:
            json.dump({
                'image_id': image_id,
                'keypoints': payload['keypoints'],
                'image_metadata': payload['image_metadata'],
            }, handle, ensure_ascii=False, indent=2)

        response_data = {
            'success': True,
            'message': 'Imagen y keypoints guardados exitosamente.',
            'image_id': image_id,
            'created_at': timezone.now().isoformat(),
            'storage_path': _relative_media_path('images', 'processed', storage_filename),
        }
        return Response(response_data, status=status.HTTP_200_OK)


class VideoAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = VideoUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # Allow filtering by user for video uploads
        if self.request.user and self.request.user.is_authenticated:
            return VideoUpload.objects.filter(idUsuario=self.request.user)
        return VideoUpload.objects.none()

    def perform_create(self, serializer):
        serializer.save(idUsuario=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        serializer = VideoUploadFormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        video_file = serializer.validated_data['video']
        token = _timestamp_token()
        ext = os.path.splitext(video_file.name)[1].lower() or '.mp4'
        filename = f'video_{token}{ext}'
        relative_path = default_storage.save(os.path.join('videos', 'uploads', filename), video_file)
        absolute_path = _media_abs_path(relative_path)

        capture = cv2.VideoCapture(absolute_path)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        duration_seconds = float(frame_count / fps) if fps else None
        capture.release()

        id_usuario = None
        if getattr(request, 'user', None) is not None and getattr(request.user, 'is_authenticated', False):
            id_usuario = getattr(request.user, 'idUsuario', None) or getattr(request.user, 'pk', None)

        video_upload = VideoUpload.objects.create(
            idUsuario_id=id_usuario,
            idEmpresa=None,
            nombreOriginal=video_file.name,
            rutaArchivo=relative_path,
            tamanioBytes=video_file.size,
            duracionSegundos=duration_seconds,
            fps=fps or None,
            estado='PENDING',
            celeryTaskId=None,
        )

        return Response(VideoUploadSerializer(video_upload).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        video = self.get_object()
        serializer = VideoProcessingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        mode = serializer.validated_data['mode']
        dimension = serializer.validated_data['dimension']
        fps_skip = serializer.validated_data['fps_skip']
        confidence_threshold = serializer.validated_data['confidence_threshold']

        try:
            video.estado = 'PROCESSING'
            video.celeryTaskId = str(uuid.uuid4())
            video.fechaProcesamiento = timezone.now()
            video.save()

            analysis = analyze_video_behavior(
                video_path=os.path.join(os.fspath(settings.MEDIA_ROOT), video.rutaArchivo),
                mode=mode,
                dimension=dimension,
                fps_skip=fps_skip,
                confidence_threshold=confidence_threshold,
            )

            with transaction.atomic():
                detections_created = []
                for detection_data in analysis['detections']:
                    detection = DetectionEvent.objects.create(
                        idVideoUpload=video,
                        tipoEvento=detection_data['tipo_evento'],
                        confianza=detection_data['confianza'],
                        frameInicio=detection_data['frame_inicio'],
                        frameFin=detection_data['frame_fin'],
                        tiempoInicio=detection_data['segundo_inicio'],
                        tiempoFin=detection_data['segundo_fin'],
                        personasInvolucradas=detection_data.get('personas_involucradas', 1),
                        detalles=detection_data.get('detalles', {}),
                        usuarioCreacion=str(getattr(request.user, 'idUsuario', 'Sistema')) if request and hasattr(request, 'user') else 'Sistema',
                    )
                    detections_created.append(detection)

                    for kp_payload in analysis.get('person_keypoints', []):
                        if kp_payload.get('frame_index') == detection_data['frame_inicio']:
                            PersonKeypoints.objects.create(
                                idDetectionEvent=detection,
                                personId=kp_payload['person_id'],
                                frameNumber=kp_payload['frame_index'],
                                keypointsJson=kp_payload['keypoints_json'],
                                usuarioCreacion=str(getattr(request.user, 'idUsuario', 'Sistema')) if request and hasattr(request, 'user') else 'Sistema',
                            )

                report, _ = AnalysisReport.objects.get_or_create(
                    idVideoUpload=video,
                    defaults={
                        'idEmpresa': video.idEmpresa,
                        'totalFrames': analysis['total_frames'],
                        'totalDuracionSegundos': analysis['duration_seconds'],
                        'totalEventos': len(analysis['detections']),
                        'totalPeleas': sum(1 for item in analysis['detections'] if item['tipo_evento'] == 'PELEA'),
                        'totalDisturbios': sum(1 for item in analysis['detections'] if item['tipo_evento'] == 'DISTURBIO'),
                        'confianzaPromedio': analysis['summary'].get('average_confidence', 0),
                        'confianzaMaxima': analysis['summary'].get('max_confidence', 0),
                        'tiempoProcesamientoSegundos': analysis['processing_time_seconds'],
                        'estadisticas': analysis['summary'],
                        'resumenJson': analysis['summary'],
                        'usuarioCreacion': str(getattr(request.user, 'idUsuario', 'Sistema')) if request and hasattr(request, 'user') else 'Sistema',
                    },
                )
                report.totalFrames = analysis['total_frames']
                report.totalDuracionSegundos = analysis['duration_seconds']
                report.totalEventos = len(analysis['detections'])
                report.totalPeleas = sum(1 for item in analysis['detections'] if item['tipo_evento'] == 'PELEA')
                report.totalDisturbios = sum(1 for item in analysis['detections'] if item['tipo_evento'] == 'DISTURBIO')
                report.confianzaPromedio = analysis['summary'].get('average_confidence', 0)
                report.confianzaMaxima = analysis['summary'].get('max_confidence', 0)
                report.tiempoProcesamientoSegundos = analysis['processing_time_seconds']
                report.estadisticas = analysis['summary']
                report.resumenJson = analysis['summary']
                report.usuarioModificacion = str(getattr(request.user, 'idUsuario', 'Sistema')) if request and hasattr(request, 'user') else 'Sistema'
                report.save()

                processed_filename = f'video_processed_{video.idVideoUpload}.mp4'
                processed_absolute_path = _media_abs_path('videos', 'results', processed_filename)
                _ensure_parent_dir(processed_absolute_path)
                shutil.copy2(os.path.join(os.fspath(settings.MEDIA_ROOT), video.rutaArchivo), processed_absolute_path)

            video.estado = 'COMPLETED'
            video.fechaProcesamiento = timezone.now()
            video.save(update_fields=['estado', 'fechaProcesamiento'])

            response_data = {
                'id': video.idVideoUpload,
                'status': 'processing',
                'task_id': video.celeryTaskId,
                'message': 'Procesamiento iniciado',
                'started_at': timezone.now(),
            }
            return Response(VideoProcessingResponseSerializer(response_data).data, status=status.HTTP_202_ACCEPTED)

        except Exception as exc:
            video.estado = 'FAILED'
            video.save(update_fields=['estado'])
            return Response({'error': 'Processing failed', 'message': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        video = self.get_object()

        try:
            analysis = analyze_video_behavior(
                video_path=os.path.join(os.fspath(settings.MEDIA_ROOT), video.rutaArchivo),
                mode=request.query_params.get('mode', 'operativo'),
                dimension=request.query_params.get('dimension', '2D'),
                fps_skip=int(request.query_params.get('fps_skip', 1)),
                confidence_threshold=float(request.query_params.get('confidence_threshold', 0.75)),
            )
        except Exception as exc:
            def error_stream():
                yield f'event: error\ndata: {json.dumps({"error": "Processing failed", "message": str(exc)}, ensure_ascii=False)}\n\n'

            return StreamingHttpResponse(error_stream(), content_type='text/event-stream', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        def event_stream():
            progress_payload = {
                'video_id': video.idVideoUpload,
                'progress_percent': 100,
                'current_frame': analysis['total_frames'],
                'total_frames': analysis['total_frames'],
                'processing_time_elapsed_sec': analysis['processing_time_seconds'],
                'eta_seconds': 0,
                'timestamp': timezone.now(),
            }
            yield f'event: progress\ndata: {json.dumps(SSEProgressEventSerializer(progress_payload).data, ensure_ascii=False, default=str)}\n\n'

            for detection in analysis['detections']:
                detection_payload = {
                    'frame_index': detection['frame_inicio'],
                    'timestamp_sec': detection['segundo_inicio'],
                    'detections': [detection],
                    'bounding_boxes': detection.get('bounding_boxes', []),
                    'frame_base64': detection.get('frame_base64', ''),
                }
                yield f'event: detection\ndata: {json.dumps(SSEDetectionEventSerializer(detection_payload).data, ensure_ascii=False)}\n\n'

            completed_payload = {
                'video_id': video.idVideoUpload,
                'status': 'completed',
                'total_detections': len(analysis['detections']),
                'total_processing_time_sec': analysis['processing_time_seconds'],
                'detections_summary': analysis['summary'].get('detections_by_type', {}),
            }
            yield f'event: completed\ndata: {json.dumps(SSECompletedEventSerializer(completed_payload).data, ensure_ascii=False, default=str)}\n\n'

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        return response

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        video = self.get_object()
        detections = DetectionEvent.objects.filter(idVideoUpload=video).order_by('frameInicio', 'fechaCreacion')
        report = AnalysisReport.objects.filter(idVideoUpload=video).first()

        response_data = {
            'id': video.idVideoUpload,
            'filename': video.nombreOriginal,
            'status': video.estado.lower(),
            'processing_mode': request.query_params.get('mode', 'operativo'),
            'total_frames': report.totalFrames if report else 0,
            'duration_seconds': video.duracionSegundos or 0,
            'processing_time_seconds': report.tiempoProcesamientoSegundos if report else 0,
            'detections': DetectionEventSerializer(detections, many=True).data,
            'analysis_report': AnalysisReportSerializer(report).data if report else None,
            'created_at': video.fechaCarga,
            'updated_at': video.fechaProcesamiento or video.fechaCarga,
        }

        return Response(VideoResultsSerializer(response_data).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        video = self.get_object()
        output_format = request.query_params.get('format', 'mp4').lower()
        processed_path = _media_abs_path('videos', 'results', f'video_processed_{video.idVideoUpload}.{output_format}')
        if not os.path.exists(processed_path):
            processed_path = os.path.join(os.fspath(settings.MEDIA_ROOT), video.rutaArchivo)

        if not os.path.exists(processed_path):
            return Response({'error': 'Video not found', 'message': 'El video procesado no está disponible.'}, status=status.HTTP_404_NOT_FOUND)

        filename = f'video_processed_{video.idVideoUpload}.{output_format}'
        return FileResponse(open(processed_path, 'rb'), as_attachment=True, filename=filename)


class FrameGenerationViewSet(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], url_path='generate-from-video')
    def generate_from_video(self, request):
        serializer = GenerateFramesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Datos inválidos', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        video_file = serializer.validated_data['video']
        fps_value = serializer.validated_data['fps_value']
        max_duration_seconds = serializer.validated_data['max_duration_seconds']
        token = _timestamp_token()
        ext = os.path.splitext(video_file.name)[1].lower() or '.mp4'
        relative_path = default_storage.save(os.path.join('videos', 'uploads', f'frames_{token}{ext}'), video_file)
        absolute_path = _media_abs_path(relative_path)

        try:
            frames = generate_frames_from_video(
                video_path=absolute_path,
                fps_value=fps_value,
                max_duration_seconds=max_duration_seconds,
            )
        except Exception as exc:
            return Response({'error': 'Processing failed', 'message': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = {
            'video_filename': video_file.name,
            'fps_extracted': fps_value,
            'total_frames_generated': len(frames),
            'duration_seconds': frames[-1]['timestamp_sec'] if frames else 0,
            'frames': frames,
            'processing_time_ms': 0,
            'message': f'Frames generados exitosamente. Total: {len(frames)} imágenes.',
        }
        return Response(GenerateFramesResponseSerializer(response_data).data, status=status.HTTP_200_OK)


