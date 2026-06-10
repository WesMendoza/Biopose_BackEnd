import os
from celery import Celery

# Establecer las configuraciones predeterminadas de Django para celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('biopose')

# Usar configuraciones de Django. El namespace='CELERY' significa que 
# todas las claves de configuración de celery deben tener el prefijo 'CELERY_'.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carga automáticamente tareas desde todos los archivos tasks.py en las apps instaladas.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
