import os
from app.models.database import DATABASE_URL

def test_database_url():
    # Simula las variables de entorno para las pruebas
    DB_USER=os.getenv("DB_USER","example")
    DB_PASSWORD= os.getenv("DB_PASSWORD","example")
    DB_HOST=os.getenv("DB_HOST","localhost")
    DB_PORT=os.getenv("DB_PORT",5434)
    DB_NAME=os.getenv("DB_NAME","example")
    
    expected_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    assert DATABASE_URL == expected_url