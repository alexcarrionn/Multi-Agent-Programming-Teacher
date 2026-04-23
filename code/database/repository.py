from datetime import datetime
import uuid
from sqlalchemy import create_engine, text

from sqlalchemy.orm import sessionmaker
from database.models import AlumnoAula, Base, Alumno, Progreso, Interaccion
from database.hash_password import hash_password, verify_password
from config.settings import settings
from i18n import setup_i18n
import pandas as pd

_ = setup_i18n("es")

# URL de conexión estándar de SQLAlchemy para MySQL
DATABASE_URL = (
    f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
)

#para depurar la conexion y saber que todo va bien 
#engine = create_engine(DATABASE_URL, echo=True)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#funcion para crear las tablas en la base de datos MySQL utilizando SQLAlchemy
def create_tables():
    Base.metadata.create_all(bind=engine)
    print(_("TABLES CREATED SUCCESSFULLY"))


#definimos una funcion para comprobar que las tablas existen en la base de datos MySQL
def tablas_existen() -> bool:
    session = SessionLocal()
    try:
        result = session.execute(text("SHOW TABLES;"))
        tables = [row[0] for row in result.fetchall()]
        return "alumnos" in tables and "progresos" in tables and "alumnos_aula" in tables and "interacciones" in tables
    finally:
        session.close()

#Comprobamos la conexión a la base de datos MySQL y mostramos el nombre de la base de datos a la que estamos conectados
def check_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE();"))
            db_name = result.fetchone()[0]
            print(_("DATABASE CONNECTION SUCCESSFULLY") + f" {db_name}")
            return True
    except Exception as e:
        print(f"{_('DATABASE CONNECTION ERROR')}: {e}")
        return False

#Comprobamos si existe un schema (base de datos) con el nombre dado en MySQL
def schema_exists():
    """Crea la base de datos si no existe."""
    # conexión al servidor sin DB, primero conectamos con el servidor MYSQL
    server_url = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
    #creamos el engine para conectarnos al servidor MYSQL
    engine = create_engine(server_url, echo=False)
    try:
        with engine.connect() as connection:
            #Una vez nos conectamos, comprobamos si la base de datos existe, si no existe la creamos
            connection.execute(
                text(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DB}")
            )
            connection.commit()
            return True
    finally:
        engine.dispose()

#Funcion que nos va a servir para conseguir la conexion a la base de datos.
def get_connection():
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        print(f"{_('DATABASE CONNECTION ERROR')}: {e}")
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

def register_alumno(email: str, plain_password: str, nombre: str, nivel: str) -> Alumno:
    """
    Registra un nuevo alumno en la base de datos MySQL.
    Lanza una excepción ValueError si el email ya está registrado.
    Devuelve el objeto Alumno registrado.
    """
    session = SessionLocal()
    try:
        existing_alumno = session.query(Alumno).filter(Alumno.email == email).first()
        if existing_alumno is not None:
            raise ValueError(_("EMAIL ALREADY REGISTERED"))
        
        new_alumno = Alumno(
            email=email,
            password=hash_password(plain_password), 
            nombre=nombre,
            nivel=nivel
        )
        session.add(new_alumno)
        session.commit()
        session.refresh(new_alumno)
        return new_alumno
    finally:
        session.close()    

#Funcion en la que el agente supervisor va a comprobar que el email introducido por el alumno esta en la base de datos creada con el excel
#que el docente ha proporcionado con los alumnos autorizados para usar el agente docente, si el email no esta en esa bbdd 
# el alumno no podra registrarse ni iniciar sesion
def comprobacion_email(correo: str) -> bool:
    #Antes se comprobaba que el email estaba en un excel, pero ahora se va a comrpobar en la base de datos MySQL, en la tabla AlumnoAula, que se ha rellenado previamente con los datos de los alumnos autorizados a usar el agente docente.
    #ruta = os.path.join(os.path.dirname(__file__), "..", "data", "alumnos_autorizados.xlsx")
    #df = pd.read_excel(ruta)
    #return email in df["Correo"].values
    session = SessionLocal()
    try: 
        alumno_aula = session.query(AlumnoAula).filter(AlumnoAula.correo == correo).first()
        return alumno_aula is not None
    finally:
        session.close()  

#Función para actualizar la base de datos MySQL
def actualizar_base_datos(path: str):
    session = SessionLocal()
    try: 
        df = pd.read_excel(path)
        # Limpiamos la tabla AlumnoAula antes de insertar los nuevos datos
        session.query(AlumnoAula).delete()
        session.commit()
        # Insertamos los nuevos datos del excel en la tabla AlumnoAula
        for idx, row in df.iterrows():
            nombre = None if pd.isna(row.get("Nombre")) else str(row.get("Nombre")).strip()
            correo = None if pd.isna(row.get("Correo electrónico")) else str(row.get("Correo electrónico")).strip()
            dni = None if pd.isna(row.get("DNI")) else str(row.get("DNI")).strip()

            # Nombre y correo son obligatorios para evitar errores de integridad.
            if not nombre or not correo:
                continue

            alumno_aula = AlumnoAula(
                nombre=nombre,
                correo=correo,
                dni=dni
            )
            session.add(alumno_aula)
        session.commit()
    except Exception as e:
        print(f"{_('ERROR SAVING USERS')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()  

#Funcion que utilizaran los agentes evaluador y critico para guardar en la base de datos MySQL el progreso del alumno.
def guardar_progreso(alumno_id: int, enunciado_ejercicio: str = None, codigo_alumno: str = None, puntuacion_ejercicio: str = None, retroalimentacion_ejercicio: str = None, ambito_dificultad: str = None): 
    """Funcion que sirve para guardar en la base de datos 
    MySQL el progreso del alumno, incluyendo los aspectos claves de este"""
    session = SessionLocal()
    try:
        progreso_alumno = Progreso(
            alumno_id=alumno_id,
            enunciado_ejercicio=enunciado_ejercicio,
            codigo_alumno=codigo_alumno,
            puntuacion_ejercicio=puntuacion_ejercicio,
            retroalimentacion_ejercicio=retroalimentacion_ejercicio,
            fecha_evaluacion=datetime.now(),
            ambito_dificultad=ambito_dificultad
        )
        session.add(progreso_alumno)
        session.commit()
        session.refresh(progreso_alumno)
        return progreso_alumno
    except Exception as e:
        print(f"{_('ERROR SAVING PROGRESS')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()  

#definimos una nueva funcion para que los agentes puedan cambiar el nivel del alumno segun vean conveniente
def cambio_nivel(nivel:str, alumno_id: int):
    #conectamos a la base de datos MySQL utilizando la sesión de SQLAlchemy
    session = SessionLocal()
    try:
        #buscamos el alumno con id a cambiar
        alumno = session.query(Alumno).filter(Alumno.id == alumno_id).first()
        #si se encuentra el alumno, se cambia el nivel de este. 
        if alumno is not None:
            alumno.nivel = nivel
            session.commit()
            session.refresh(alumno)
            return alumno
        #Si no se encuentra el alumno se lanza un mensaje de error. 
        else:
            raise ValueError(_("ALUMNO NOT FOUND"))
    except Exception as e:
        print(f"{_('ERROR CHANGING LEVEL')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()

#definimos una funcion para cambiar la contraseña de un alumno en la base de datos
def update_password(alumno_id: int, new_password: str):
    session = SessionLocal()
    try:
        alumno = session.query(Alumno).filter(Alumno.id == alumno_id).first()
        if alumno is not None:
            alumno.password = hash_password(new_password)
            session.commit()
            session.refresh(alumno)
            return alumno
        else:
            raise ValueError(_("ALUMNO NOT FOUND"))
    except Exception as e:
        print(f"{_('ERROR UPDATING PASSWORD')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()
"""
Esta funcion la dejaremos por si en un futuro queremos eliminar el progreso del alumno al eliminar su cuenta, 
aunque por ahora se ha optado por una estrategia de anonimización de los datos del alumno, 
en lugar de eliminar completamente su cuenta y progreso, para cumplir con las normativas de protección de datos y permitir la conservación 
de información relevante para el análisis del uso del agente docente.

#implementamos una funcion para eliminar la cuenta de un alumno en la base de datos MySQL
def eliminar_cuenta_alumno(alumno_id: int):
    session = SessionLocal()
    try:
        alumno = session.query(Alumno).filter(Alumno.id == alumno_id).first()
        if alumno is not None:
            session.delete(alumno)
            session.commit()
        else:
            raise ValueError(_("ALUMNO NOT FOUND"))
    except Exception as e:
        print(f"{_('ERROR DELETING ACCOUNT')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()
"""

def eliminar_cuenta_alumno(alumno_id: int):
    session = SessionLocal()
    try:
        alumno = session.query(Alumno).filter(Alumno.id == alumno_id).first()
        if alumno is None:
            raise ValueError(_("ALUMNO NOT FOUND"))

        email_anonimizado = f"anonimo_{alumno.id}_{uuid.uuid4().hex[:8]}@anonimizado.local"
        alumno.email = email_anonimizado
        alumno.nombre = "Alumno Anonimizado"
        alumno.password = "CUENTA_ELIMINADA"
        alumno.anonimizado = True
        alumno.fecha_anonimizacion = datetime.now()

        session.commit()
    except Exception as e:
        print(f"{_('ERROR DELETING ACCOUNT')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def guardar_interaccion(alumno_id: int, mensaje_usuario: str, respuesta_agente: str, tipo_interaccion: str):
    session = SessionLocal()
    try:
        interaccion = Interaccion(
            alumno_id=alumno_id,
            mensaje_usuario=mensaje_usuario,
            respuesta_agente=respuesta_agente,
            tipo_interaccion=tipo_interaccion,
            fecha_interaccion=datetime.now()
        )
        session.add(interaccion)
        session.commit()
    except Exception as e:
        print(f"Error guardando interacción: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def get_interacciones(alumno_id: int):
    session = SessionLocal()
    try:
        return session.query(Interaccion).filter(
            Interaccion.alumno_id == alumno_id
        ).order_by(Interaccion.fecha_interaccion.desc()).all()
    finally:
        session.close()