import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from watchfiles  import watch, Change
import threading
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


# Aseguramos que la raíz del proyecto esté en sys.path para poder importar load_data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth.auth import create_access_token, get_current_user
from database.repository import actualizar_base_datos, comprobacion_email, create_tables, register_alumno, authenticate_alumno, tablas_existen, schema_exists
from graph.workflow import stream_graph_updates
from i18n import setup_i18n
from load_data import SUPPORTED_FORMATS ,eliminar_documentacion, indexar_documentos, actualizar_documentacion, load_documents_from_folder

DATA_PATH = Path(__file__).resolve().parent / "data" / "Introduccion_programacion"
DATA_AUTORITHED_USER_PATH = Path(__file__).resolve().parent / "data" / "alumnos_autorizados.xlsx"

#Configuramos la internacionalización para mostrar los mensajes en el idioma del usuario, en este caso español
_= setup_i18n("es")

"""Definimos WatchFiles para que se recargue la base de datos MySQL cada vez que se modifique el excel 
 con los alumnos autorizados, de esta forma el docente puede añadir o eliminar alumnos autorizados 
 sin necesidad de reiniciar el agente docente, simplemente modificando el excel y guardándolo, con la 
 condición de que el excel tenga la misma estructura que el original (con las columnas "Nombre", "Correo" y "DNI")."""

def observar_cambios_archivos():
    for changes in watch(DATA_AUTORITHED_USER_PATH.parent):
        for change_type, path in changes:
            # En Windows, guardar desde Excel suele generar eventos added + modified.
            if change_type in (Change.added, Change.modified) and Path(path).resolve()== DATA_AUTORITHED_USER_PATH:
                actualizar_base_datos(str(DATA_AUTORITHED_USER_PATH))


#Funcion para observar los cambios en la carpeta de DATA_PATH, para poder recargar los documentos en la base de datos vectorial de QDrant
#cada vez que añadamos o modifiquemos un nuevo documento. 

def observar_cambios_documentacion():
    #tenemos que hacerlo de forma recursiva para observar los cambios en las subcarpetas de DATA_PATH
    for changes in watch(DATA_PATH):
        for change_type, path in changes:

            file_path = Path(path).resolve()
            
            #Evitamos que sean ficheros que no sean aceptados por la funcion de carga de documentos.
            if file_path.suffix.lower() not in SUPPORTED_FORMATS:
                continue

            if change_type == Change.added:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                indexar_documentos(file_path, DATA_PATH.parent)
            elif change_type == Change.modified:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                actualizar_documentacion(file_path, DATA_PATH.parent)
            elif change_type == Change.deleted:
                eliminar_documentacion(file_path, DATA_PATH.parent)




#Funcion principal que se encargará de manejar el ciclo de vida de la app para los hilos del observador de cambios en los archivos y el stream de actualizaciones del grafo de conocimiento.
@asynccontextmanager
async def lifespan(app: FastAPI):
    #indicamos que se ha iniciado el servidor
    print(_("SERVER STARTED"))

    #Comprobamos que las tablas de la base de datos MySQL existen, si no existen las creamos
    schema_exists()
    #Después tenemos que construir la base de datos mySql con la tabla de alumnos y progreso, para ello verficiamos primero si se existen ya el schema y las tablas
    #Si no existen las creamos si existen no hacemos nada 
    if not tablas_existen():
        create_tables()
    
    print (_("INITIALIZE THREADS"))
    #Ahora inicializamos los hilos observadores 
    hilo_observador_alumnos = threading.Thread(target=observar_cambios_archivos, daemon=True)
    hilo_observador_documentacion = threading.Thread(target=observar_cambios_documentacion, daemon=True)
    hilo_observador_alumnos.start()
    hilo_observador_documentacion.start()

    #Ahora el servidor le cede el control y se pone a escuchar peticiones 
    yield

#Creamos la Api con FastApi
app = FastAPI(
    title="Codi - Agente Docente de Programación",
    description="BackEnd para el agente educador",
    lifespan=lifespan
)

#configuramos CORS para permitir peticiones desde el frontend, en este caso desde localhost:3000, pero esto se puede cambiar cuando se despliegue el frontend en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Cambiar esto por el dominio de tu frontend en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#Definimos una funcion en la que se registre un usuario
class AlumnoCreate(BaseModel):
    nombre: str
    email: str
    password: str
    nivel: str


@app.post("/api/register")
async def registrar_alumno(datos: AlumnoCreate):

    """Esta funcion recibirá los datos de registro del alumno desde el frontend, comprobará el email y si es correcto lo registrará"""
    if not datos.email.endswith("@um.es"):
       raise HTTPException(status_code=400, detail=_("ERROR INVALID EMAIL DOMAIN"))
    
    #Ponemos la logica de comprobacion de email autorizado 
    if not comprobacion_email(datos.email):
        raise HTTPException(status_code=400, detail=_("ERROR EMAIL NOT AUTHORIZED"))
    
    #Si el email es correcto y esta autorizado, registramos al alumno en la base de datos MySQL
    try: 
        register_alumno(email=datos.email, plain_password=datos.password, nombre=datos.nombre, nivel=datos.nivel)
        return {"message": _("REGISTRATION SUCCESS")}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=_("REGISTRATION ERROR") + f": {str(e)}")

class AlumnoLogin(BaseModel):
    email: str
    password: str

#definimos la funcion que comprobará las credenciales del alumno para poder iniciar sesión, ademas 
# usaremos el token del alumno para mantener la sesión iniciada y poder mostrar su progreso y personalizar su experiencia.
@app.post("/api/login")
def login_alumno(datos: AlumnoLogin, response: Response):
    """Esta funcion se encargará de autenticar al alumno y devolver un token de acceso para mantener la sesión iniciada"""
    alumno = authenticate_alumno(datos.email, datos.password)
    if not alumno:
        raise HTTPException(status_code=401, detail=_("ERROR INVALID CREDENTIALS"))
    
    # Generar token de acceso
    token = create_access_token({
        "sub": alumno.email,
        "nombre": alumno.nombre,
        "nivel": alumno.nivel,
        "alumno_id": alumno.id,
        })
    
    #creamos la respuesta que se le va a dar al frontend
    response.set_cookie(key="access_token", 
                        value=token, 
                        httponly=True, 
                        secure=False, 
                        samesite="lax",     #Esto se puede cambiar cuando usemos HHTPS en producción, para mejorar la seguridad
                        max_age=3600)
    
    return {"message": _("LOGIN SUCCESS")}

#Definimos una funcion que nos devuelva los datos del alumno actual a partir del token 
@app.get("/api/me")
def obtener_datos_alumno_actual(current_user: dict = Depends(get_current_user)):
    """Esta funcion se encargará de devolver los datos del alumno actual a partir del token de acceso"""
    return {"email": current_user["sub"], "nombre": current_user["nombre"], "nivel": current_user["nivel"], "alumno_id": current_user["alumno_id"]}

#Definimos una funcion para poder cerrar la sesion del alumno actual, eliminamos la cookie. 
@app.post("/api/logout")
def logout_alumno(response: Response):
    """Esta funcion se encargará de cerrar la sesión del alumno"""
    response.delete_cookie(key="access_token")
    return {"message": _("GOODBYE MESSAGE")}
