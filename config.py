import os

class Config:
    # =========================================
    # CONFIGURACIÓN CON VARIABLES DE ENTORNO (Docker)
    # =========================================
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.environ.get('DB_PORT', 5432))
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
    DB_NAME = os.environ.get('DB_NAME', 'canchas')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave_secreta_para_jwt_USAT_2025__**01')

    # =========================================
    # CONFIGURACIÓN LOCAL (sin Docker)
    # Descomentar estas líneas y comentar las de arriba
    # =========================================
    # DB_HOST = '127.0.0.1'
    # DB_PORT = 5432
    # DB_USER = 'postgres'
    # DB_PASSWORD = '123456789'
    # DB_NAME = 'BdFutbol_Jayanca'
    # SECRET_KEY = 'clave_secreta_para_jwt_USAT_2025__**01'

    # =========================================
    # CONFIGURACIÓN SUPABASE (producción)
    # =========================================
    # DB_HOST = 'aws-1-us-east-2.pooler.supabase.com'
    # DB_PORT = 5432
    # DB_USER = 'postgres.vozpbtnbaliaecedqgvb'
    # DB_PASSWORD = 'jayanca2025'
    # DB_NAME = 'postgres'
    # SECRET_KEY = 'clave_secreta_para_jwt_USAT_2025__**01'

