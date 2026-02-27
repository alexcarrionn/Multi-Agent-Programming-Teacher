from database.repository import comprobacion_email, register_alumno, authenticate_alumno
from langgraph.workflow import stream_graph_updates

#Definimos una funcion en la que se registre un usuario
def registrar_alumno():
    email = input("Introduce tu correo: ")
    #Primero comprobamos que el email es de la um 
    if not email.endswith("@um.es"):
        print("Error: el correo introducido no es válido. Por favor, introduce un correo de la Universidad de Murcia (terminado en @um.es).\n")
        return
    #Comprobamos que el email este en el excel puesto por el docente
    comprobacion = comprobacion_email(email)
    if not comprobacion:
        print("Error: el correo introducido no está autorizado para registrarse. Por favor, contacta con tu docente para obtener acceso.\n")
        return
    else: 
        password = input("Introduce tu contraseña: ")
        nombre = input("Introduce tu nombre: ")
        nivel = input("Introduce tu nivel (principiante, intermedio, avanzado, etc...): ")
        # Registramos al alumno en la base de datos MySQL
        try:
            register_alumno(email, password, nombre, nivel)
            print("Registro completado con éxito.")
        except ValueError as e:
            print(f"Error en el registro: {e}")


#Funcion principal para ejecutar el workflow del agente docente
if __name__ == "__main__":
    #Bucle para poder identificar al usuario
    while True:
        user_input = input("Bienvenido al agente docente. Escribe 'iniciar sesion' para comenzar o 'registrarse' para poder crear una cuenta (o 'salir' para salir): ")
        if user_input.lower() == "salir":
            print("Saliendo del agente docente. ¡Hasta luego!")
            break
        elif user_input.lower() == "registrarse":
           registrar_alumno()
        elif user_input.lower() == "iniciar sesion":
            email = input("Introduce tu correo: ")
            password = input("Introduce tu contraseña: ")

            # Validamos las credenciales contra la base de datos MySQL
            alumno = authenticate_alumno(email, password)
            if alumno is None:
                print("Error: credenciales incorrectas. Inténtalo de nuevo.\n")
                continue

            print(f"Bienvenido, {alumno.nombre} (nivel: {alumno.nivel or 'sin definir'})\n")

            # Usamos el email como thread_id para persistir la conversación por alumno
            thread_id = alumno.email

            # Bucle de conversación para el alumno autenticado
            while True:
                user_input = input("Introduce tu mensaje (o 'salir'): ")
                if user_input.lower() == "salir":
                    print("Saliendo del agente docente. ¡Hasta luego!")
                    break
                stream_graph_updates(user_input, thread_id)
            break
        else: 
            print("Opción no válida. Por favor, escribe 'iniciar sesion', 'registrarse' o 'salir'.\n")
