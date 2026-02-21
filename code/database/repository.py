from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from database.models import Base, Alumno
from database.hash_password import verify_password
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

#Funcion para poder encontrar a un alumno por su email 
def get_alumno_by_email(email: str) -> Alumno | None:
    """Busca un alumno por su email. Devuelve el objeto Alumno o None."""
    session = SessionLocal()
    try:
        return session.query(Alumno).filter(Alumno.email == email).first()
    finally:
        session.close()

#Funcion para autenticar a un alumno utilizando su email y contraseña, verificando las credenciales contra la base de datos MySQL
def authenticate_alumno(email: str, plain_password: str) -> Alumno | None:
    """
    Autentica a un alumno contra la base de datos MySQL.
    Devuelve el objeto Alumno si las credenciales son correctas, o None en caso contrario.
    """
    alumno = get_alumno_by_email(email)
    if alumno is None:
        return None
    if not verify_password(plain_password, alumno.password):
        return None
    return alumno