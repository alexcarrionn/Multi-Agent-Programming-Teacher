from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from database.models import Base
from config.settings import settings

# URL de conexión estándar de SQLAlchemy para MySQL
DATABASE_URL = (
    f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#funcion para crear las tablas en la base de datos MySQL utilizando SQLAlchemy
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")

#Comprobamos la conexión a la base de datos MySQL y mostramos el nombre de la base de datos a la que estamos conectados
def check_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE();"))
            db_name = result.fetchone()[0]
            print(f"Conectado a la base de datos: {db_name}")
            return True
    except Exception as e:
        print(f"Error al conectar a la base de datos MySQL: {e}")
        return False


#Funcion que nos va a servir para conseguir la conexion a la base de datos.
def get_connection():
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        print(f"Error en la conexión a la base de datos: {e}")
        session.rollback()
        raise
    finally:
        session.close()