import socket
import tkinter as tk
from tkinter import messagebox

def open_waiting_room(logged_in_users, username):
    # Crear una nueva ventana para la sala de espera
    waiting_room = tk.Toplevel(window)
    waiting_room.title("Sala de Espera")
    waiting_room.geometry("300x400")
    waiting_room.configure(bg="#D8BFD8")

    font_tlt = "Indie Flower"

    # Título de la sala de espera
    label_waiting = tk.Label(waiting_room, text="Sala de Espera", bg="#D8BFD8", fg="black", font=(font_tlt, 20))
    label_waiting.pack(pady=20)

    # Mostrar usuarios logueados con botones de "Retar"
    for user in logged_in_users:
        if user != username:  # Excluir al usuario que inició sesión
            frame_user = tk.Frame(waiting_room, bg="#D8BFD8")
            frame_user.pack(pady=5)
            label_user = tk.Label(frame_user, text=user, bg="#D8BFD8", fg="black", font=(font_tlt, 15))
            label_user.pack(side=tk.LEFT)
            button_challenge = tk.Button(
                frame_user, 
                text="Retar", 
                bg="#C99AF5", 
                font=(font_tlt, 12),
                command=lambda u=user: start_game(u, username, waiting_room)  # Pasa el oponente y usuario
            )
            button_challenge.pack(side=tk.LEFT, padx=10)

def start_game(opponent, username, waiting_room):
    # Cerrar la sala de espera
    waiting_room.destroy()
    # Abrir la ventana del gato con el usuario actual y el oponente seleccionado
    open_cat_window(username, opponent)

def open_cat_window(username, opponent):
    # Crear una nueva ventana para el gato
    cat_window = tk.Toplevel(window)
    cat_window.title("Juego del Gato")
    cat_window.geometry("400x700")
    cat_window.configure(bg="#D8BFD8")
    
    font_tlt = "Indie Flower"

    # Variables de turno
    current_turn = tk.StringVar(value=username)  # Turno inicial es del usuario que inició sesión

    # Cabecera de turnos
    label_turn = tk.Label(cat_window, textvariable=current_turn, font=(font_tlt, 20), bg="#D8BFD8")
    label_turn.pack(pady=10)
    
    # Puntaje (izquierda - derecha)
    score_frame = tk.Frame(cat_window, bg="#D8BFD8")
    score_frame.pack(pady=10)
    
    label_player1 = tk.Label(score_frame, text=f"{username}", font=(font_tlt, 18), bg="#D8BFD8")
    label_player1.pack(side=tk.LEFT, padx=20)
    
    label_score = tk.Label(score_frame, text="0-0", font=(font_tlt, 18), bg="#D8BFD8")  # Puntaje inicial
    label_score.pack(side=tk.LEFT, padx=20)
    
    label_player2 = tk.Label(score_frame, text=f"{opponent}", font=(font_tlt, 18), bg="#D8BFD8")
    label_player2.pack(side=tk.LEFT, padx=20)

    # Tablero del gato (grid de botones)
    board_frame = tk.Frame(cat_window, bg="#D8BFD8")
    board_frame.pack(pady=20)
    
    board_buttons = []
    def button_click(i, j):
        # Verificar si el cuadro está vacío y asignar el turno actual
        if board_buttons[i][j]["text"] == "":
            board_buttons[i][j]["text"] = "X" if current_turn.get() == username else "O"
            # Cambiar el turno
            next_turn = opponent if current_turn.get() == username else username
            current_turn.set(f"Turno de: {next_turn}")

    for i in range(3):
        row = []
        for j in range(3):
            button = tk.Button(
                board_frame, text="", font=(font_tlt, 20),
                width=5, height=2, bg="#D3A4F5",
                command=lambda x=i, y=j: button_click(x, y)
            )
            button.grid(row=i, column=j, padx=5, pady=5)
            row.append(button)
        board_buttons.append(row)
    
    # Mensaje de ganador (inicialmente oculto)
    label_winner = tk.Label(cat_window, text="", font=(font_tlt, 20), bg="#D8BFD8")
    label_winner.pack(pady=10)

    # Botones para acciones (Jugar de nuevo y Salir)
    action_frame = tk.Frame(cat_window, bg="#D8BFD8")
    action_frame.pack(pady=10)

    button_restart = tk.Button(action_frame, text="Jugar de nuevo", font=(font_tlt, 15), bg="#C99AF5", command=lambda: print("Reiniciar juego"))
    button_restart.pack(side=tk.LEFT, padx=10)
    
    button_exit = tk.Button(action_frame, text="Salir", font=(font_tlt, 15), bg="#A575CC", command=cat_window.destroy)
    button_exit.pack(side=tk.LEFT, padx=10)

def authenticate():
    # Obtener los valores ingresados
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        try:
            # Crear socket del cliente
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 9999))

            # Enviar usuario y contraseña
            credentials = f"{username},{password}"
            client.send(credentials.encode('utf-8'))

            # Recibir respuesta del servidor
            response = client.recv(1024).decode('utf-8')
            print(response)
            if response.startswith("Autenticación exitosa"):
                logged_in_users = response.split(',')[1:]
                open_waiting_room(logged_in_users, username)  # Abrir la sala de espera
            else:
                messagebox.showinfo("Resultado", response)
        except Exception as e:
            print(f"Error: {e}")
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingrese usuario y contraseña.")

# Crear la ventana principal
window = tk.Tk()
window.title("Autenticación")
window.configure(bg='#D45DE1')

font_tlt = "Indie Flower"

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
