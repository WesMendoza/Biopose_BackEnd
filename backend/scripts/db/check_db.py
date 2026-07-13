import os
import sys
import django
from django.db import connection

# Configurar el entorno de Django para poder importar configuraciones y modelos
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.normpath(os.path.join(script_dir, '..', '..'))
sys.path.append(backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
try:
    django.setup()
except Exception as e:
    print(f"[ERROR] Al inicializar Django: {e}")
    print("Asegurate de estar en el entorno virtual activo (venv) e importar las dependencias.")
    sys.exit(1)

def check_database():
    expected_tables = [
        'users', 
        'empresa', 
        'rol', 
        'menuOption', 
        'systemParameter',
        'empresaUsuarioRol', 
        'rolOption', 
        'parametrosCabecera', 
        'parametroDetalle',
        'analysisImageUpload', 
        'analysisVideoUpload', 
        'analysisDetectionEvent',
        'analysisPersonKeypoints', 
        'analysisReport'
    ]
    
    django_tables = [
        'django_migrations', 
        'django_content_type', 
        'django_session',
        'auth_permission', 
        'auth_group', 
        'django_admin_log'
    ]
    
    print("\n=======================================================")
    print("COMPROBADOR DE BASE DE DATOS - BIOPOSE")
    print("=======================================================")
    
    # 1. Comprobar Conexión
    try:
        connection.ensure_connection()
        db_settings = connection.settings_dict
        print(f"[OK] Conexion establecida correctamente con PostgreSQL.")
        print(f"   Base de datos: {db_settings.get('NAME')}")
        print(f"   Host:          {db_settings.get('HOST')}")
        print(f"   Esquema (Dev): {db_settings.get('OPTIONS', {}).get('options', 'No definido')}")
    except Exception as e:
        print(f"[ERROR] De conexion a PostgreSQL: {e}")
        print("   Verifica las credenciales en tu archivo .env o .env.local.")
        return
        
    # 2. Leer las tablas existentes en la BD
    try:
        with connection.cursor() as cursor:
            db_tables = connection.introspection.table_names(cursor)
    except Exception as e:
        print(f"[ERROR] Al leer el catalogo de tablas: {e}")
        return
        
    # 3. Validar Tablas del Negocio (Definidas en el Script SQL)
    found_expected = []
    missing_expected = []
    db_tables_lower = [t.lower() for t in db_tables]
    
    for table in expected_tables:
        if table.lower() in db_tables_lower:
            found_expected.append(table)
        else:
            missing_expected.append(table)
            
    print(f"\nTABLAS DEL PROYECTO (SQL / Modelos): ({len(found_expected)}/{len(expected_tables)})")
    for table in found_expected:
        print(f"   [OK]     {table}")
        
    if missing_expected:
        print(f"\n[FALTA] TABLAS DEL PROYECTO FALTANTES:")
        for table in missing_expected:
            print(f"   [FALTA]  {table}")
        print("\nSugerencia: Crea las tablas corriendo el script 'CreateDb.sql' o ejecuta 'python manage.py migrate'.")
    else:
        print("\n   Todas las tablas del negocio estan creadas correctamente!")
        
    # 4. Validar Tablas del Sistema de Django (Sesiones, Migraciones, etc.)
    found_django = []
    missing_django = []
    for table in django_tables:
        if table.lower() in db_tables_lower:
            found_django.append(table)
        else:
            missing_django.append(table)
            
    print(f"\nTABLAS DE CONTROL DE DJANGO: ({len(found_django)}/{len(django_tables)})")
    for table in found_django:
        print(f"   [OK]     {table}")
        
    if missing_django:
        print(f"\n   [INFO] Faltan algunas tablas internas de Django.")
        print("   Solucion: Ejecuta en tu consola:")
        print("      python manage.py migrate --fake-initial")
    else:
        print("\n   [OK] El sistema de Django tiene todas sus tablas de control listas.")
    print("=======================================================\n")

if __name__ == '__main__':
    check_database()
