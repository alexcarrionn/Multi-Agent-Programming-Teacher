from database.repository import comprobacion_email, register_alumno, authenticate_alumno
from graph.workflow import stream_graph_updates
from i18n import setup_i18n

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
            # Bucle de conversación para el alumno autenticado
            while True:
                user_input = input(_("INPUT MESSAGE"))
                if user_input.lower() == _("EXIT"):
                    print(_("GOODBYE MESSAGE"))
                    break
                
                stream_graph_updates(user_input, thread_id, user_level)
            break
        else: 
            print(_("INVALID OPTION MESSAGE"))