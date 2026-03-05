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
