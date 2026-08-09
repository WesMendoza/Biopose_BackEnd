import os
import io
import time
from locust import HttpUser, task, between

class BioPosePerformanceUser(HttpUser):
    # Host por defecto (Django Backend)
    host = "http://localhost:8000"

    # Simula un tiempo de espera aleatorio entre peticiones de cada usuario
    wait_time = between(1, 5)
    
    # Credenciales de prueba (se pueden configurar por variables de entorno)
    CORREO = os.getenv("BIOPOSE_TEST_EMAIL", "admin@biopose.com")
    PASSWORD = os.getenv("BIOPOSE_TEST_PASSWORD", "admin123")
    
    token = None


    def on_start(self):
        """
        Método que se ejecuta al inicio de la simulación para cada usuario virtual.
        Realiza el login y obtiene el token JWT para autenticar las llamadas subsecuentes.
        """
        self.login()

    def login(self):
        payload = {
            "correo": self.CORREO,
            "password": self.PASSWORD
        }
        with self.client.post("/api/auth/login/", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    # Extraer token de la estructura: detalle -> token
                    self.token = res_json.get("detalle", {}).get("token")
                    if self.token:
                        response.success()
                    else:
                        response.failure("Token no encontrado en la respuesta de login.")
                except Exception as e:
                    response.failure(f"Error al parsear respuesta de login: {str(e)}")
            else:
                response.failure(f"Login fallido con estado {response.status_code}: {response.text}")

    @property
    def auth_headers(self):
        """Retorna las cabeceras de autorización con el Token JWT."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @task(3)
    def test_image_upload_and_analysis(self):
        """
        Simula la carga y análisis síncrono de una imagen.
        """
        if not self.token:
            self.login()
            if not self.token:
                return

        # Generar una imagen de 1x1 píxeles (GIF válido) en memoria para no depender de archivos locales
        dummy_gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'
        files = {
            "image": ("locust_test.gif", dummy_gif_bytes, "image/gif")
        }

        with self.client.post(
            "/api/analysis/media/images/upload/",
            headers=self.auth_headers,
            files=files,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Subida de imagen fallida (Estado {response.status_code}): {response.text}")

    @task(1)
    def test_video_upload_and_processing_flow(self):
        """
        Simula el flujo completo de video:
        1. Subir video (upload)
        2. Iniciar procesamiento asíncrono (process)
        3. Consultar resultados periódicamente (polling de results)
        """
        if not self.token:
            self.login()
            if not self.token:
                return

        # Para pruebas de carga reales de procesamiento de video, se recomienda usar un video real muy corto
        # (ej: de 1-2 segundos en formato mp4) guardado en la carpeta de la prueba.
        # Si no existe, usamos una cadena dummy de bytes para probar la subida de archivos (pero fallará en la IA).
        video_filename = "test_video_short.mp4"
        video_path = os.path.join(os.path.dirname(__file__), video_filename)

        if os.path.exists(video_path):
            with open(video_path, "rb") as vf:
                video_data = vf.read()
        else:
            video_data = b"DUMMY_MP4_DATA_FOR_LOAD_TESTING"
            video_filename = "dummy_short.mp4"

        files = {
            "video": (video_filename, video_data, "video/mp4")
        }

        # 1. Subir el video
        video_id = None
        with self.client.post(
            "/api/analysis/media/videos/upload/",
            headers=self.auth_headers,
            files=files,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                try:
                    video_id = response.json().get("idVideoUpload")
                    response.success()
                except Exception as e:
                    response.failure(f"Error al extraer idVideoUpload: {str(e)}")
                    return
            else:
                response.failure(f"Subida de video fallida (Estado {response.status_code}): {response.text}")
                return

        # 2. Iniciar procesamiento (si el upload fue exitoso y obtuvimos el ID)
        if video_id:
            process_payload = {
                "mode": "operativo",
                "dimension": "2D",
                "fps_skip": 5,
                "confidence_threshold": 0.75,
                "analysis_type": "multipersona"
            }
            
            with self.client.post(
                f"/api/analysis/videos/{video_id}/process/",
                headers=self.auth_headers,
                json=process_payload,
                catch_response=True
            ) as proc_response:
                if proc_response.status_code != 202:
                    proc_response.failure(f"Error al encolar procesamiento para video {video_id}: {proc_response.text}")
                    return
                proc_response.success()

            # 3. Consultar resultados (Polling)
            max_polls = 15
            for i in range(max_polls):
                # Esperar antes de consultar (damos tiempo a Celery para procesar)
                time.sleep(3)
                
                # Agrupamos el endpoint en Locust usando el parámetro `name` para no llenar el reporte
                with self.client.get(
                    f"/api/analysis/videos/{video_id}/results/",
                    headers=self.auth_headers,
                    name="/api/analysis/videos/[id]/results/",
                    catch_response=True
                ) as poll_response:
                    if poll_response.status_code == 200:
                        try:
                            status_val = poll_response.json().get("status")
                            if status_val == "completed":
                                poll_response.success()
                                break
                            elif status_val == "failed":
                                poll_response.failure("El procesamiento de IA falló en Celery.")
                                break
                            else:
                                poll_response.success()
                        except:
                            poll_response.failure("Error al parsear JSON de resultados.")
                            break
                    elif poll_response.status_code == 202:
                        # Aún procesando (PROCESSING)
                        poll_response.success()
                    else:
                        poll_response.failure(f"Error de consulta de estado: {poll_response.status_code}")
                        break
