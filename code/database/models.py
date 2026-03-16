from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT as longText
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()
"""
Aqui vamos a definir las tabalas que vamos a utilizar en la base de datos MySQL, 
vamos a tener una tabla de alumnos y una tabla de progresos.
cada alumno puede tener un progreso asociado 
que almacena su avance en los ejercicios, sus puntuaciones, retroalimentación y el ámbito donde mas dificultad tenga.
"""
class Alumno(Base):
    __tablename__ = 'alumnos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    nivel = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    progreso = relationship("Progreso", back_populates="alumno", cascade="all, delete-orphan")

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
