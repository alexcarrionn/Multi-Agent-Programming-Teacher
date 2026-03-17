import sys
from pathlib import Path
from watchfiles  import watch, Change
import threading
import time
from database.repository import actualizar_base_datos

# Aseguramos que la raíz del proyecto esté en sys.path para poder importar load_data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.repository import comprobacion_email, create_tables, register_alumno, authenticate_alumno, tablas_existen, schema_exists
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
                indexar_documentos(file_path, DATA_PATH)
            elif change_type == Change.modified:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                actualizar_documentacion(file_path, DATA_PATH)
            elif change_type == Change.deleted:
                eliminar_documentacion(file_path, DATA_PATH)

#Definimos una funcion en la que se registre un usuario
def registrar_alumno():
    email = input(_("INPUT EMAIL"))
    #Primero comprobamos que el email es de la um 
    if not email.endswith("@um.es"):
        print(_("ERROR EMAIL NOT FROM UM"))
        return
    #Comprobamos que el email este en la base de datos puesto por el docente
    comprobacion = comprobacion_email(email)
    if not comprobacion:
        print(_("ERROR EMAIL NOT AUTHORIZED"))
        return
    else: 
        password = input(_("INPUT PASSWORD"))
        nombre = input(_("INPUT NAME"))
        nivel = input(_("INPUT LEVEL"))
        
        # Registramos al alumno en la base de datos MySQL
        try:
            register_alumno(email, password, nombre, nivel)
            print(_("REGISTRATION SUCCESS"))
        except ValueError as e:
            print(_("REGISTRATION ERROR") + f" {e}")


#Funcion principal para ejecutar el workflow del agente docente
if __name__ == "__main__":
    #En un hilo aprate al principal, observamos los cambios en el excel de los alumnos autorizados
    #con daemon se cerrara automáticamente el hilo cuando se cierre el progrma principal.
    hilo_observador = threading.Thread(target=observar_cambios_archivos, daemon=True)
    hilo_observador.start()
    #Primero creamos el SCHEMA de la base de datos donde van a estar las tablas de alumnos y progreso, si ya existe no hacemos nada
    schema_exists()
    #Despué tenemos que construir la base de datos mySql con la tabla de alumnos y progreso, para ello verficiamos primero si se existen ya el schema y las tablas
    #Si no existen las creamos si existen no hacemos nada 
    existen_tablas = tablas_existen()
    if not existen_tablas:
        create_tables()

    #Si existe el excel con los alumnos lo cargamos en la base de datos
    if DATA_AUTORITHED_USER_PATH.exists():
        actualizar_base_datos(DATA_AUTORITHED_USER_PATH)
    #Una vez hecho la bbdd MySQL, metemos los documentos en la base de datos de vectores de QDrant 
    #data_root = Path(__file__).resolve().parent / "data"
    #para poder cambiar de asignatura solo hay que cambiar el nombre de la carpeta, siempre y cuando se mantenga la estructura de carpetas dentro de data
    #load_documents_from_folder(data_root / "Introduccion_programacion", data_root)

    #Ahora tenemos que crear otro hilo diferente para poder observar los cambios en la carpeta de data, para poder recargar 
    # los documentos en la base de datos de vectores de QDrant cada vez que se añadan nuevos documentos o se modifiquen los existentes, 
    # de esta forma el agente docente siempre tendra la información actualizada sin necesidad de reiniciar el programa.
    hilo_observador_data = threading.Thread(target=observar_cambios_documentacion, daemon=True)
    hilo_observador_data.start()

    #Bucle para poder identificar al usuario
    while True:
        user_input = input(_("WELCOME MESSAGE"))
        if user_input.lower() == _("EXIT"):
            print(_("GOODBYE MESSAGE"))
            break
        elif user_input.lower() == _("REGISTER"):
           registrar_alumno()
        elif user_input.lower() == _("LOGIN"):
            email = input(_("INPUT EMAIL"))
            password = input(_("INPUT PASSWORD"))

            # Validamos las credenciales contra la base de datos MySQL
            alumno = authenticate_alumno(email, password)
            if alumno is None:
                print(_("ERROR INVALID CREDENTIALS"))
                continue

            print(_("WELCOME USER") + f" {alumno.nombre}\n")

            # Usamos el email como thread_id para persistir la conversación por alumno
            thread_id = alumno.email
            user_level = alumno.nivel
            alumno_id = alumno.id
            # Bucle de conversación para el alumno autenticado
            while True:
                user_input = input(_("INPUT MESSAGE"))
                if user_input.lower() == _("EXIT"):
                    print(_("GOODBYE MESSAGE"))
                    break
                
                stream_graph_updates(user_input, thread_id, user_level, alumno_id)
            break
        else: 
            print(_("INVALID OPTION MESSAGE"))