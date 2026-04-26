from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT as longText
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()
"""
Aqui vamos a definir las tabalas que vamos a utilizar en la base de datos MySQL, 
vamos a tener una tabla de alumnos y una tabla de progresos.
cada alumno puede tener un progreso asociado 
que almacena su avance en los ejercicios, sus puntuaciones, retroalimentación y el ámbito donde mas dificultad tenga.
"""

"""
Esta clase alumno se queda en el caso en el que un futuro se quiera borrar el progreso del alumno al borrar la cuenta 
class Alumno(Base):
    __tablename__ = 'alumnos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    nivel = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    progreso = relationship("Progreso", back_populates="alumno", cascade="all, delete-orphan")
"""
class Alumno(Base):
    __tablename__ = 'alumnos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    nivel = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    anonimizado = Column(Boolean, default=False, nullable=False)
    fecha_anonimizacion = Column(DateTime, nullable=True)
    progreso = relationship("Progreso", back_populates="alumno")
    interacciones = relationship("Interaccion", back_populates="alumno")

class Progreso(Base):
    """
    Se pone una fila por cada ejercicio evaluado. 
    Asi mantenemos el historial completo del progreso del alumno.
    """
    __tablename__ = 'progresos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alumno_id = Column(Integer, ForeignKey('alumnos.id'), nullable=False)
    enunciado_ejercicio = Column(longText, nullable=True)
    codigo_alumno = Column(longText, nullable=True)
    puntuacion_ejercicio = Column(longText, nullable=True) 
    retroalimentacion_ejercicio = Column(longText, nullable=True)
    fecha_evaluacion = Column(DateTime, nullable=True)
    ambito_dificultad = Column(String(255), nullable=True)
 
    alumno = relationship("Alumno", back_populates="progreso")


class AlumnoAula(Base): 
    """
    Tabla que identifica a los alumnos para poder comprobar si tienen acceso al agente docente o no. Esta tabla se va a sacar a 
    través de un proceso de estracción de datos del aula virtual, donde se entraerá un excel con el nombre del alumno, 
    su email y el dni (no es obligatorio). 
    """
    __tablename__ = 'alumnos_aula'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(255), unique=True, nullable=False)
    dni = Column(String(20), nullable=True)

class Interaccion(Base): 
    """En esta tabla se van a almacenar las interacciones que tenga el alumno con el agente docente, 
    ya no solo va a existir ese progreso que va a hacer sino que tambien se va a poder visualizar todo lo que el alumno 
    ha preguntado al agente docente, las respuestas de este y la fecha de cada interacción."""
    __tablename__ = 'interacciones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alumno_id = Column(Integer, ForeignKey('alumnos.id'), nullable=False)
    mensaje_usuario = Column(longText, nullable=True)
    respuesta_agente = Column(longText, nullable=True)
    fecha_interaccion = Column(DateTime, nullable=True)
    tipo_interaccion = Column(String(50), nullable=True)  # Por ejemplo: "consulta", "retroalimentación", etc.
    asignatura = Column(String(100), nullable=True)  # Para identificar a qué asignatura se refiere la interacción

    alumno = relationship("Alumno", back_populates="interacciones")

