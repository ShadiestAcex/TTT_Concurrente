import socket 
import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage

def authenticate():
    #Obtener los valores ingresados
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        try:
            #Crear socket del cliente
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 9999))

            #Enviar usuario y contraseña
            credentials = f"{username},{password}"
            client.send(credentials.encode('utf-8'))

            #Recibir respuesta del servidor
            response = client.recv(1024).decode('utf-8')
            print(response)
            if response == "Autenticación exitosa":
                open_waiting_room()
            else:
                messagebox.showinfo("Resultado", response)
        except Exception as e:
            print(f"Error: {e}")
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingrese ususario y contraseña.")

def open_waiting_room():
    # Crear una nueva ventana para la sala de espera
    waiting_room = tk.Toplevel(window)
    waiting_room.title("Sala de Espera")
    waiting_room.configure(bg='#D8BFD8')

    label_waiting = tk.Label(waiting_room, text="Esperando a otros jugadores...", bg="#D8BFD8", fg="white", font=("Arial", 20))
    label_waiting.pack(pady=20)

    # Aquí puedes agregar más widgets o lógica para la sala de espera

# Crear la ventana principal
window = tk.Tk()
window.title("Autenticación")

# Establecer el fondo de color sólido
window.configure(bg='#D45DE1')

font_tlt="Indie Flower"

# Crear otros widgets encima del fondo
label_texto = tk.Label(window, text="TIK-TAK-TOE", fg="white", bg="#D45DE1", font=(font_tlt, 60))
label_texto.pack(pady=5)
label_texto1 = tk.Label(window, text="UPP", fg="white", bg="#D45DE1", font=(font_tlt, 60))
label_texto1.pack(pady=10)

label_username = tk.Label(window, text="Usuario", bg="#D45DE1", font=(font_tlt, 30))
label_username.pack(pady=5)
entry_username = tk.Entry(window)
entry_username.pack(pady=5)

label_password = tk.Label(window, text="Contraseña", bg="#D45DE1", font=(font_tlt, 30))
label_password.pack(pady=5)
entry_password = tk.Entry(window, show="*")
entry_password.pack(pady=5)

# Botón para autenticar
button_login = tk.Button(window, text="Iniciar", command=authenticate, font=(font_tlt, 30))
button_login.pack(pady=20)

# Iniciar el bucle principal de la interfaz gráfica
window.mainloop()

#To do: Ventana del tiktaktoe
