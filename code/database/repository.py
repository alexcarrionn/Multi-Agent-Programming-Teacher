from datetime import datetime
import uuid
from sqlalchemy import create_engine, text
import io
from sqlalchemy.orm import sessionmaker
from database.models import AlumnoAulaAsignatura, Base, Alumno, DocenteAula, Progreso, Interaccion, Docente, Asignatura, DocenteAsignatura, AlumnoAsignatura
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
        return (
            "alumnos" in tables
            and "progresos" in tables
            and "interacciones" in tables
            and "docentes" in tables
            and "docentes_aula" in tables
            and "asignaturas" in tables
            and "docentes_asignaturas" in tables
            and "alumnos_asignaturas" in tables
            and "alumnos_aula_asignatura" in tables
        )
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

#funcion para poder encontrar a un docente por su email
def get_docente_by_email(email: str) -> Docente | None:
    """Busca un docente por su email. Devuelve el objeto Docente o None."""
    session = SessionLocal()
    try:
        return session.query(Docente).filter(Docente.email == email).first()
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

#Funcion para autenticar al docente \
def authenticate_docente(email: str, plain_password: str) -> Docente | None:
    """
    Autentica a un docente contra la base de datos MySQL.
    Devuelve el objeto Docente si las credenciales son correctas, o None en caso contrario.
    """
    docente = get_docente_by_email(email)
    if docente is None:
        return None
    if not verify_password(plain_password, docente.password):
        return None
    return docente

def register_alumno(email: str, plain_password: str, nombre: str, nivel: str) -> Alumno:
    """
    Registra un nuevo alumno y lo matricula automáticamente en todas las asignaturas
    donde su correo aparezca en AlumnoAulaAsignatura (autorizaciones del docente).
    Lanza ValueError si el email ya está registrado.
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
        session.flush()  # rellena new_alumno.id sin cerrar la transacción

        # Auto-matricular en todas las asignaturas donde el correo este autorizado
        autorizaciones = session.query(AlumnoAulaAsignatura).filter(
            AlumnoAulaAsignatura.correo == email
        ).all()
        for autorizacion in autorizaciones:
            session.add(AlumnoAsignatura(
                alumno_id=new_alumno.id,
                asignatura_id=autorizacion.asignatura_id
            ))

        session.commit()
        session.refresh(new_alumno)
        return new_alumno
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

#funcion para registar a un nuevo docente en la base de datos MySQL
def register_docente(email: str, plain_password: str, nombre: str) -> Docente:
    """
    Registra un nuevo docente en la base de datos MySQL.
    Lanza una excepción ValueError si el email ya está registrado.
    Devuelve el objeto Docente registrado.
    """
    session = SessionLocal()
    try:
        existing_docente = session.query(Docente).filter(Docente.email == email).first()
        if existing_docente is not None:
            raise ValueError(_("EMAIL ALREADY REGISTERED"))
        
        new_docente = Docente(
            email=email,
            password=hash_password(plain_password),
            nombre=nombre,
            rol="docente"
        )
        session.add(new_docente)
        session.commit()
        session.refresh(new_docente)
        return new_docente
    finally:
        session.close()  

#Comprueba que el correo del alumno esta autorizado a registrarse en al menos una asignatura.
#Cada docente gestiona su propia lista de autorizados desde el panel (subida de Excel o CRUD manual).
def comprobacion_email_alumno(correo: str) -> bool:
    session = SessionLocal()
    try:
        autorizado = session.query(AlumnoAulaAsignatura).filter(
            AlumnoAulaAsignatura.correo == correo
        ).first()
        return autorizado is not None
    finally:
        session.close()

#Comprueba que el correo del docente esta autorizado, mirando la tabla DocenteAula que se rellena con el excel de docentes_autorizados.xlsx.
def comprobacion_email_docente(correo: str) -> bool:
    session = SessionLocal()
    try:
        docente_aula = session.query(DocenteAula).filter(DocenteAula.correo == correo).first()
        return docente_aula is not None
    finally:
        session.close()

#Funcion que va a permitir actualizar la base de datos de los docentes
def actualizar_base_datos_docentes(path: str):
    session = SessionLocal()
    try: 
        df = pd.read_excel(path)
        # Limpiamos la tabla Docente antes de insertar los nuevos datos
        session.query(DocenteAula).delete()
        session.commit()
        # Insertamos los nuevos datos del excel en la tabla DocenteAula
        for idx, row in df.iterrows():
            nombre = None if pd.isna(row.get("Nombre")) else str(row.get("Nombre")).strip()
            correo = None if pd.isna(row.get("Correo electrónico")) else str(row.get("Correo electrónico")).strip()
            dni = None if pd.isna(row.get("DNI")) else str(row.get("DNI")).strip()

            # Nombre y correo son obligatorios para evitar errores de integridad.
            if not nombre or not correo:
                continue

            docente = DocenteAula(
                nombre=nombre,
                correo=correo,
                dni=dni
            )
            session.add(docente)
        session.commit()
    except Exception as e:
        print(f"{_('ERROR SAVING TEACHERS')}: {e}")
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

def guardar_interaccion(alumno_id: int, mensaje_usuario: str, respuesta_agente: str, tipo_interaccion: str, asignatura: str):
    session = SessionLocal()
    try:
        interaccion = Interaccion(
            alumno_id=alumno_id,
            mensaje_usuario=mensaje_usuario,
            respuesta_agente=respuesta_agente,
            tipo_interaccion=tipo_interaccion,
            fecha_interaccion=datetime.now(),
            asignatura=asignatura
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

#definimos la funcion para poder obtener las asignaturas por cliente 
def get_asignaturas_por_docente(docente_id: int) -> list[Asignatura]:
      session = SessionLocal()
      try:
          return (
              session.query(Asignatura)
              .join(DocenteAsignatura, DocenteAsignatura.asignatura_id == Asignatura.id)
              .filter(DocenteAsignatura.docente_id == docente_id)
              .all()
          )
      finally:
          session.close()


def crear_asignatura(nombre: str,codigo: str, docente_id: int) -> Asignatura:
    """Crea una asignatura y la asocia al docente que la crea."""
    session = SessionLocal()
    try:
          # Comprobar que no existe ya una asignatura con ese código
          existing = session.query(Asignatura).filter(Asignatura.codigo == codigo).first()
          if existing is not None:
              raise ValueError(_("ASIGNATURA ALREADY EXISTS"))

          nueva = Asignatura(nombre=nombre, codigo=codigo)
          session.add(nueva)
          session.flush()  # asigna el id sin cerrar la transacción

          relacion = DocenteAsignatura(docente_id=docente_id, asignatura_id=nueva.id)
          session.add(relacion)

          session.commit()
          session.refresh(nueva)
          return nueva
    except Exception as e:
          session.rollback()
          raise
    finally:
          session.close()

def get_alumnos_por_asignatura(asignatura_id: int) -> list[Alumno]:
    "Devuelve los alumnos matriculados en una asignatura, excluyendo cuentas anonimizadas."
    session = SessionLocal()
    try:
        return (
            session.query(Alumno)
            .join(AlumnoAsignatura, AlumnoAsignatura.alumno_id == Alumno.id)
            .filter(AlumnoAsignatura.asignatura_id == asignatura_id)
            .filter(Alumno.anonimizado == False)
            .all()
        )
    finally:
        session.close()

def matricular_alumno_en_asignatura(alumno_id: int, asignatura_id: int) -> AlumnoAsignatura:
    """Matricula un alumno en una asignatura creando una fila en la tabla intermedia AlumnoAsignatura."""
    session = SessionLocal()
    try:
        alumno = session.query(Alumno).filter(Alumno.id == alumno_id).first()
        asignatura = session.query(Asignatura).filter(Asignatura.id == asignatura_id).first()

        if alumno is None:
            raise ValueError(_("ALUMNO NOT FOUND"))
        if asignatura is None:
            raise ValueError(_("ASIGNATURA NOT FOUND"))

        # Si ya existe la matrícula, no la duplicamos (UniqueConstraint la rechazaría igualmente).
        existing = session.query(AlumnoAsignatura).filter(
            AlumnoAsignatura.alumno_id == alumno_id,
            AlumnoAsignatura.asignatura_id == asignatura_id,
        ).first()
        if existing is not None:
            raise ValueError(_("ALUMNO ALREADY ENROLLED"))

        matricula = AlumnoAsignatura(alumno_id=alumno_id, asignatura_id=asignatura_id)
        session.add(matricula)
        session.commit()
        session.refresh(matricula)
        return matricula
    except Exception as e:
        print(f"{_('ERROR ENROLLING STUDENT')}: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def get_progreso_alumno(alumno_id: int) -> list[Progreso]:
      session = SessionLocal()
      try:
          return session.query(Progreso).filter(
              Progreso.alumno_id == alumno_id
          ).order_by(Progreso.fecha_evaluacion.desc()).all()
      finally:
          session.close()


#Vamos a crear una funcion para poder hacer UPSERT en la tabla de alumno autorizados en la bbdd
def import_alumnos_autorizados_excel(asignatura_id: int, df) -> tuple[int, int]:
    session = SessionLocal()
    insertador = 0
    actualizados = 0 
    try: 
        for idx, row in df.iterrows():
            nombre = None if pd.isna(row.get("Nombre")) else str(row.get("Nombre")).strip()
            correo = None if pd.isna(row.get("Correo electrónico")) else str(row.get("Correo electrónico")).strip()
            dni = None if pd.isna(row.get("DNI")) else str(row.get("DNI")).strip()

            if not nombre or not correo:
                continue

            existente = session.query(AlumnoAulaAsignatura).filter(
                AlumnoAulaAsignatura.asignatura_id == asignatura_id,
                AlumnoAulaAsignatura.correo == correo
            ).first()

            if existente is not None:
                existente.nombre = nombre
                existente.dni = dni
                actualizados += 1
            else:
                nuevo = AlumnoAulaAsignatura(
                    asignatura_id=asignatura_id,
                    nombre=nombre,
                    correo=correo,
                    dni=dni
                )
                session.add(nuevo)
                insertador += 1

        session.commit()
        return insertador, actualizados
    except Exception: 
        session.rollback()
        raise
    finally:
        session.close()

def crear_alumno_autorizado(asignatura_id: int, nombre: str, correo: str, dni: str | None = None) -> AlumnoAulaAsignatura:
      session = SessionLocal()
      try:
          existing = session.query(AlumnoAulaAsignatura).filter(
              AlumnoAulaAsignatura.asignatura_id == asignatura_id,
              AlumnoAulaAsignatura.correo == correo,
          ).first()
          if existing is not None:
              raise ValueError(_("ALUMNO ALREADY AUTHORIZED"))

          nuevo = AlumnoAulaAsignatura(
              asignatura_id=asignatura_id,
              nombre=nombre,
              correo=correo,
              dni=dni,
          )
          session.add(nuevo)
          session.commit()
          session.refresh(nuevo)
          return nuevo
      except Exception:
          session.rollback()
          raise
      finally:
          session.close()

def get_alumnos_autorizados(asignatura_id: int) -> list[AlumnoAulaAsignatura]:
      session = SessionLocal()
      try:
          return session.query(AlumnoAulaAsignatura).filter(
              AlumnoAulaAsignatura.asignatura_id == asignatura_id
          ).order_by(AlumnoAulaAsignatura.nombre).all()
      finally:
          session.close()

def get_alumno_autorizado_by_id(autorizado_id: int) -> AlumnoAulaAsignatura | None:
      session = SessionLocal()
      try:
          return session.query(AlumnoAulaAsignatura).filter(
              AlumnoAulaAsignatura.id == autorizado_id
          ).first()
      finally:
          session.close()

def actualizar_alumno_autorizado(id: int, nombre: str, correo: str, dni: str | None = None) -> AlumnoAulaAsignatura:
      # busca por id; si no existe ValueError; actualiza nombre/correo/dni; commit; return
        session = SessionLocal()
        try:
            existente = session.query(AlumnoAulaAsignatura).filter(
                AlumnoAulaAsignatura.id == id
            ).first()
            if existente is None:
                raise ValueError(_("ALUMNO AUTHORIZED NOT FOUND"))

            # Comprobar que el nuevo correo no está ya autorizado para otra cuenta (salvo si es el mismo registro)
            if existente.correo != correo:
                conflicto = session.query(AlumnoAulaAsignatura).filter(
                    AlumnoAulaAsignatura.asignatura_id == existente.asignatura_id,
                    AlumnoAulaAsignatura.correo == correo,
                    AlumnoAulaAsignatura.id != id
                ).first()
                if conflicto is not None:
                    raise ValueError(_("ANOTHER STUDENT ALREADY AUTHORIZED WITH THIS EMAIL"))

            existente.nombre = nombre
            existente.correo = correo
            existente.dni = dni
            session.commit()
            session.refresh(existente)
            return existente
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

def eliminar_alumno_autorizado(autorizado_id: int):
        session = SessionLocal()
        try:
            existente = session.query(AlumnoAulaAsignatura).filter(
                AlumnoAulaAsignatura.id == autorizado_id
            ).first()
            if existente is None:
                raise ValueError(_("ALUMNO AUTHORIZED NOT FOUND"))
    
            session.delete(existente)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()