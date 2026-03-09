import sys
from pathlib import Path

# Aseguramos que la raíz del proyecto esté en sys.path para poder importar load_data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.repository import comprobacion_email, create_tables, register_alumno, authenticate_alumno, tablas_existen, schema_exists
from graph.workflow import stream_graph_updates
from i18n import setup_i18n
from load_data import load_documents_from_folder

#Configuramos la internacionalización para mostrar los mensajes en el idioma del usuario, en este caso español
_= setup_i18n("es")

#Definimos una funcion en la que se registre un usuario
def registrar_alumno():
    email = input(_("INPUT EMAIL"))
    #Primero comprobamos que el email es de la um 
    if not email.endswith("@um.es"):
        print(_("ERROR EMAIL NOT FROM UM"))
        return
    #Comprobamos que el email este en el excel puesto por el docente
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
    #Primero creamos el SCHEMA de la base de datos donde van a estar las tablas de alumnos y progreso, si ya existe no hacemos nada
    schema_exists()
    #Despué tenemos que construir la base de datos mySql con la tabla de alumnos y progreso, para ello verficiamos primero si se existen ya el schema y las tablas
    #Si no existen las creamos si existen no hacemos nada 
    tablas_existen = tablas_existen();
    if not tablas_existen:
        create_tables()
    #Una vez hecho la bbdd MySQL, metemos los documentos en la base de datos de vectores de QDrant 
    data_root = Path(__file__).resolve().parent / "data"
    #para poder cambiar de asignatura solo hay que cambiar el nombre de la carpeta, siempre y cuando se mantenga la estructura de carpetas dentro de data
    load_documents_from_folder(data_root / "Introduccion_programacion", data_root)

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