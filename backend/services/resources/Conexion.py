import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

def _get_env_value(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default

def get_connection():
    """Establece y devuelve una conexión a la base de datos usando variables de entorno."""
    try:
        connection = psycopg2.connect(
            host=_get_env_value('DB_HOST', 'POSTGRES_HOST', default='localhost'),
            port=_get_env_value('DB_PORT', 'POSTGRES_PORT', default='5432'),
            dbname=_get_env_value('DB_NAME', 'POSTGRES_DB', default='DbBioPose'),
            user=_get_env_value('DB_USER', 'POSTGRES_USER', default='postgres'),
            password=_get_env_value('DB_PASSWORD', 'POSTGRES_PASSWORD', default=''),
            options=f"-c search_path={_get_env_value('DB_SCHEMA', default='Dev')}"
        )
        print("Conexión exitosa")
        return connection
    except psycopg2.Error as e:
        print(f"Error en la conexión a la base de datos: {e.pgcode} - {e.pgerror}")
        return None