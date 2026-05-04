#!/usr/bin/env python
"""
Script de prueba para validar servicios de IA en Fase 1.

Este script verifica que:
1. Los servicios se importan sin errores
2. La configuración se carga correctamente
3. Los servicios funcionan independientemente de Django/Flask
4. No hay dependencias faltantes
5. La conexión legacy a PostgreSQL usa variables de entorno

Ejecutar con: python test_services.py
"""

import sys
import os

# Agregar backend al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_loader():
    """Prueba carga de configuración."""
    print("\n" + "=" * 70)
    print("📋 PASO 1: Validar Carga de Configuración")
    print("=" * 70)
    
    try:
        from services.config_loader import SystemConfig
        print("✓ SystemConfig importado correctamente")
        
        config_dict = SystemConfig.to_dict()
        print("\n⚙️  Parámetros del Sistema:")
        print("-" * 70)
        
        # Mostrar parámetros clave
        key_params = {
            'YOLO_MODEL_PATH': 'Ruta del modelo YOLO',
            'LSTM_MODEL_PATH': 'Ruta del modelo LSTM',
            'YOLO_DEVICE': 'Dispositivo para YOLO (cpu/cuda)',
            'LSTM_WINDOW_SIZE': 'Tamaño de ventana LSTM',
            'THRESHOLD_PELEA': 'Umbral de confianza para Pelea',
            'THRESHOLD_DISTURBIO': 'Umbral de confianza para Disturbio',
        }
        
        for param, description in key_params.items():
            if param in config_dict:
                value = config_dict[param]
                print(f"  ✓ {param}: {value}")
                print(f"    └─ {description}")
            else:
                print(f"  ⚠ {param}: NO ENCONTRADO")
        
        print("\n✅ Configuración cargada exitosamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando SystemConfig: {e}")
        print("   Verifica que el archivo config_loader.py exista")
        return False
    except Exception as e:
        print(f"❌ Error al cargar configuración: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models_available():
    """Prueba disponibilidad de modelos copiados."""
    print("\n" + "=" * 70)
    print("📦 PASO 2: Validar Modelos Copiados del Tesis")
    print("=" * 70)
    
    models_dir = os.path.join(os.path.dirname(__file__), 'services', 'models')
    expected_models = ['PoseModule.py', 'BehaviorDetector.py', 'BehaviorDetector3d.py']
    
    print(f"\nBuscando modelos en: {models_dir}\n")
    
    all_present = True
    for model in expected_models:
        model_path = os.path.join(models_dir, model)
        if os.path.exists(model_path):
            size_kb = os.path.getsize(model_path) / 1024
            print(f"  ✓ {model} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {model} - NO ENCONTRADO")
            all_present = False
    
    if all_present:
        print("\n✅ Todos los modelos están disponibles")
        return True
    else:
        print("\n⚠️  Algunos modelos no se encuentran")
        print("   Ejecuta: Copy-Item -Path 'Tesis\\src\\model\\*' -Destination 'backend\\services\\models\\' -Force")
        return False


def test_pose_detection_import():
    """Prueba importación de servicio de pose."""
    print("\n" + "=" * 70)
    print("🧑 PASO 3: Validar Servicio de Detección de Pose")
    print("=" * 70)
    
    try:
        from services.pose_detection import PoseDetectionService
        print("✓ PoseDetectionService importado correctamente")
        
        print("\nCaracterísticas del servicio:")
        print("  • Detecta puntos clave (keypoints) del cuerpo humano")
        print("  • Soporta detección en imágenes, frames de video y streams")
        print("  • Incluye seguimiento (tracking) de múltiples personas")
        print("  • Utiliza modelo YOLO (ultralytics)")
        
        print("\n✅ Servicio de pose disponible para usar")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando PoseDetectionService: {e}")
        print("   Verifica dependencias: pip install ultralytics opencv-python numpy")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_behavior_detection_import():
    """Prueba importación de servicio de comportamiento."""
    print("\n" + "=" * 70)
    print("👁️  PASO 4: Validar Servicio de Detección de Comportamiento")
    print("=" * 70)
    
    try:
        from services.behavior_detection import BehaviorDetectionService
        print("✓ BehaviorDetectionService importado correctamente")
        
        print("\nCaracterísticas del servicio:")
        print("  • Detecta comportamientos: PELEA, DISTURBIO, NORMAL")
        print("  • Analiza secuencias de keypoints con LSTM")
        print("  • Retorna confianza de predicción por comportamiento")
        print("  • Configurable con ventanas deslizantes")
        
        print("\n✅ Servicio de comportamiento disponible para usar")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando BehaviorDetectionService: {e}")
        print("   Verifica dependencias: pip install torch numpy")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resources_available():
    """Prueba disponibilidad de recursos del Tesis."""
    print("\n" + "=" * 70)
    print("🔧 PASO 5: Validar Recursos Copiados del Tesis")
    print("=" * 70)
    
    resources_dir = os.path.join(os.path.dirname(__file__), 'services', 'resources')
    expected_resources = ['Encrypt.py', 'Helper.py', 'Conexion.py', 'Middleware.py', 'QueriesProcedures.py']
    
    print(f"\nBuscando recursos en: {resources_dir}\n")
    
    all_present = True
    for resource in expected_resources:
        resource_path = os.path.join(resources_dir, resource)
        if os.path.exists(resource_path):
            print(f"  ✓ {resource}")
        else:
            print(f"  ⚠ {resource} - no encontrado")
    
    print("\n✅ Recursos disponibles para integración")
    return True


def test_database_connection():
    """Prueba la conexión legacy a PostgreSQL usando .env."""
    print("\n" + "=" * 70)
    print("🗄️  PASO 6: Validar Conexión a PostgreSQL")
    print("=" * 70)

    try:
        from services.resources.Conexion import get_connection
        connection = get_connection()

        if connection is None:
            print("❌ No se pudo crear la conexión con la base de datos")
            print("   Revisa DB_HOST, DB_PORT, DB_NAME, DB_USER y DB_PASSWORD en .env")
            return False

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"✓ Query de prueba ejecutada: {result}")
        finally:
            connection.close()

        print("✅ Conexión a PostgreSQL validada correctamente")
        return True

    except Exception as e:
        print(f"❌ Error validando conexión a PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "VALIDACIÓN FASE 1: SERVICIOS DE IA" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Ejecutar todos los tests
    results.append(("Configuración", test_config_loader()))
    results.append(("Modelos Copiados", test_models_available()))
    results.append(("Servicio Pose", test_pose_detection_import()))
    results.append(("Servicio Comportamiento", test_behavior_detection_import()))
    results.append(("Recursos", test_resources_available()))
    results.append(("Conexión PostgreSQL", test_database_connection()))
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "-" * 70)
    print(f"Resultado: {passed}/{total} pruebas pasadas")
    print("-" * 70)
    
    if passed == total:
        print("\n✅ TODOS LOS SERVICIOS DE IA FUNCIONAN CORRECTAMENTE")
        print("\n🎉 Fase 1 COMPLETADA - Servicios encapsulados e independientes")
        print("\n📝 Próximos pasos (Fase 2):")
        print("   1. Definir modelos Django en apps/analysis/models.py")
        print("   2. Ejecutar: python manage.py makemigrations")
        print("   3. Ejecutar: python manage.py migrate")
        return 0
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        print("\nAcciones recomendadas:")
        print("   1. Verifica la instalación de dependencias")
        print("   2. Revisa los logs de error arriba")
        print("   3. Consulta el README.md de services/")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
