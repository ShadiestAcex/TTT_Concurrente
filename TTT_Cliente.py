import socket
import threading
import tkinter as tk
from tkinter import messagebox

def open_waiting_room(logged_in_users, username, client_socket):
    # Crear una nueva ventana para la sala de espera
    waiting_room = tk.Toplevel(window)
    waiting_room.title("Sala de Espera")
    waiting_room.geometry("300x400")
    waiting_room.configure(bg="#D8BFD8")

    font_tlt = "Indie Flower"

    # Título de la sala de espera
    label_waiting = tk.Label(waiting_room, text="Sala de Espera", bg="#D8BFD8", fg="black", font=(font_tlt, 20))
    label_waiting.pack(pady=20)

    # Frame para la lista de usuarios
    users_frame = tk.Frame(waiting_room, bg="#D8BFD8")
    users_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    # Actualizar la lista de usuarios periódicamente
    def update_user_list():
        try:
            client_socket.send("GET_USERS".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            if response.startswith("USERS"):
                _, users = response.split(',', 1)
                users = users.split(',')

                # Limpiar la lista de usuarios
                for widget in users_frame.winfo_children():
                    widget.destroy()

                # Crear botones para cada usuario
                for user in users:
                    if user != username:  # Excluir al usuario que inició sesión
                        frame_user = tk.Frame(users_frame, bg="#D8BFD8")
                        frame_user.pack(pady=5)
                        label_user = tk.Label(frame_user, text=user, bg="#D8BFD8", fg="black", font=(font_tlt, 15))
                        label_user.pack(side=tk.LEFT)
                        button_challenge = tk.Button(
                            frame_user,
                            text="Retar",
                            bg="#C99AF5",
                            font=(font_tlt, 12),
                            command=lambda u=user: send_challenge(u, client_socket)
                        )
                        button_challenge.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error actualizando la lista de usuarios: {e}")

    def periodic_update():
        update_user_list()
        waiting_room.after(3000, periodic_update)

    periodic_update()

    # Hilo para manejar otros mensajes
    def listen_for_messages():
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                if message.startswith("CHALLENGE"):
                    _, challenger = message.split(',')
                    response = messagebox.askyesno("Desafío", f"{challenger} te ha retado. ¿Aceptar?")
                    if response:
                        client_socket.send(f"ACCEPT,{challenger}".encode('utf-8'))
                        waiting_room.destroy()
                        open_cat_window(username, challenger, client_socket, is_challenger=False)
                        break
                    else:
                        client_socket.send(f"DECLINE,{challenger}".encode('utf-8'))

                elif message.startswith("ACCEPT"):
                    _, opponent = message.split(',')
                    messagebox.showinfo("Desafío aceptado", f"{opponent} ha aceptado tu desafío.")
                    waiting_room.destroy()
                    open_cat_window(username, opponent, client_socket, is_challenger=True)
                    break

            except Exception as e:
                print(f"Error en listen_for_messages: {e}")
                break

        print("Conexión cerrada.")

    # Iniciar hilo para escuchar mensajes
    threading.Thread(target=listen_for_messages, daemon=True).start()


def send_challenge(opponent, client_socket):
    client_socket.send(f"CHALLENGE,{opponent}".encode('utf-8'))


def open_cat_window(username, opponent, client_socket, is_challenger):
    # Crear una nueva ventana para el juego
    cat_window = tk.Toplevel(window)
    cat_window.title("Juego del Gato")
    cat_window.geometry("400x700")
    cat_window.configure(bg="#D8BFD8")

    font_tlt = "Indie Flower"

    # Variables de turno y estado del juego
    current_turn = tk.StringVar()
    turn_symbol = tk.StringVar()
    game_over = tk.BooleanVar(value=False)
    board_lock = threading.Lock()
    turn_semaphore = threading.Semaphore(0)
    scores = {username: 0, opponent: 0}  # Puntaje inicial

    # Función para manejar el clic de los botones del tablero
    def button_click(i, j):
        position = i * 3 + j
        with board_lock:
            if board[position] == '' and not game_over.get():
                # Registrar el movimiento
                board[position] = turn_symbol.get()
                board_buttons[i][j]["text"] = turn_symbol.get()
                board_buttons[i][j].config(state=tk.DISABLED)

                # Enviar el movimiento al servidor
                client_socket.send(f"MOVE,{position}".encode('utf-8'))

                # Deshabilitar el tablero mientras es turno del oponente
                disable_board()

                # Verificar si hay un ganador
                winner = check_winner()
                if winner:
                    game_over.set(True)
                    announce_winner(winner)
                    client_socket.send("GAME_ENDED".encode('utf-8'))
                elif '' not in board:
                    game_over.set(True)
                    announce_winner("Empate")
                    client_socket.send("GAME_ENDED".encode('utf-8'))
                else:
                    # Pasar el turno al oponente
                    current_turn.set(f"Turno de: {opponent}")
                    turn_semaphore.release()

    # Función para deshabilitar el tablero
    def disable_board():
        for row in board_buttons:
            for button in row:
                button.config(state=tk.DISABLED)

    # Función para habilitar el tablero
    def enable_board():
        for i in range(9):
            if board[i] == '':
                board_buttons[i // 3][i % 3].config(state=tk.NORMAL)

    # Función para verificar al ganador
    def check_winner():
        win_conditions = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for a, b, c in win_conditions:
            if board[a] == board[b] == board[c] != '':
                return board[a]
        return None

    # Función para reiniciar el juego
    def reset_game():
        for i in range(9):
            board[i] = ''
        for row in board_buttons:
            for button in row:
                button.config(text="", state=tk.NORMAL)

        game_over.set(False)

        if is_challenger:
            turn_symbol.set("X")
            current_turn.set(f"Turno de: {username}")
            turn_semaphore.release()
        else:
            turn_symbol.set("O")
            current_turn.set(f"Turno de: {opponent}")

        # El marcador permanece sin cambios
        label_score.config(text=f"{scores[username]}-{scores[opponent]}")


    # Función para anunciar al ganador
    def announce_winner(winner):
        disable_board()
        if winner == "Empate":
            label_turn.config(text="¡Empate!")
        else:
            label_turn.config(text=f"¡{winner} ha ganado esta ronda!")

            if winner == username:
                scores[username] += 1
            elif winner == opponent:
                scores[opponent] += 1

            # Actualiza el marcador visual
            label_score.config(text=f"{scores[username]}-{scores[opponent]}")

        # Verifica si alguien alcanzó 3 puntos
        if scores[username] == 3:
            messagebox.showinfo("Juego terminado", f"¡Felicidades {username}, ganaste el juego!")
            client_socket.send("GAME_OVER".encode('utf-8'))
            cat_window.destroy()
        elif scores[opponent] == 3:
            messagebox.showinfo("Juego terminado", f"¡{opponent} ganó el juego!")
            client_socket.send("GAME_OVER".encode('utf-8'))
            cat_window.destroy()
        else:
            # Reinicia el juego para la próxima ronda
            reset_game()


    # Crear el tablero
    board = ['' for _ in range(9)]
    board_buttons = []

    board_frame = tk.Frame(cat_window, bg="#D8BFD8")
    board_frame.pack(pady=20)

    for i in range(3):
        row = []
        for j in range(3):
            button = tk.Button(
                board_frame,
                text="",
                font=(font_tlt, 20),
                width=5,
                height=2,
                command=lambda x=i, y=j: button_click(x, y)
            )
            button.grid(row=i, column=j, padx=5, pady=5)
            row.append(button)
        board_buttons.append(row)

    # Crear encabezado de turno
    label_turn = tk.Label(cat_window, textvariable=current_turn, font=(font_tlt, 20), bg="#D8BFD8")
    label_turn.pack(pady=10)

    # Crear marco de puntaje
    score_frame = tk.Frame(cat_window, bg="#D8BFD8")
    score_frame.pack(pady=10)

    label_player1 = tk.Label(score_frame, text=f"{username}", font=(font_tlt, 18), bg="#D8BFD8")
    label_player1.pack(side=tk.LEFT, padx=20)

    label_score = tk.Label(score_frame, text="0-0", font=(font_tlt, 18), bg="#D8BFD8")
    label_score.pack(side=tk.LEFT, padx=20)

    label_player2 = tk.Label(score_frame, text=f"{opponent}", font=(font_tlt, 18), bg="#D8BFD8")
    label_player2.pack(side=tk.LEFT, padx=20)

    # Crear marco de acciones
    action_frame = tk.Frame(cat_window, bg="#D8BFD8")
    action_frame.pack(pady=10)

    # Hilo para escuchar movimientos
    def listen_for_moves():
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message.startswith("MOVE"):
                    _, position = message.split(',')
                    position = int(position)

                    symbol = 'O' if turn_symbol.get() == 'X' else 'X'

                    with board_lock:
                        board[position] = symbol
                        board_buttons[position // 3][position % 3].config(text=symbol, state=tk.DISABLED)

                    winner = check_winner()
                    if winner:
                        game_over.set(True)
                        announce_winner(winner)
                    elif '' not in board:
                        game_over.set(True)
                        announce_winner("Empate")
                    else:
                        current_turn.set(f"Turno de: {username}")
                        enable_board()
                        turn_semaphore.acquire()

                elif message.startswith("SCORE"):
                    _, score = message.split(',')
                    label_score.config(text=score)  # Actualiza el marcador en la interfaz

                elif message.startswith("GAME_OVER"):
                    _, score = message.split(',')
                    messagebox.showinfo("Juego terminado", f"El juego ha terminado. Marcador final: {score}")
                    cat_window.destroy()
                    break

            except Exception as e:
                print(f"Error recibiendo movimientos: {e}")
                break



    threading.Thread(target=listen_for_moves, daemon=True).start()
    reset_game()


def authenticate():
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 9999))
            client_socket.send(f"{username},{password}".encode('utf-8'))

            response = client_socket.recv(1024).decode('utf-8')
            if response.startswith("Autenticación exitosa"):
                logged_in_users = response.split(',')[1:]
                open_waiting_room(logged_in_users, username, client_socket)
            else:
                messagebox.showinfo("Resultado", response)
        except Exception as e:
            print(f"Error: {e}")
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingrese usuario y contraseña.")


# Ventana principal
window = tk.Tk()
window.title("Autenticación")
window.configure(bg='#D45DE1')

font_tlt = "Indie Flower"

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

button_login = tk.Button(window, text="Iniciar", command=authenticate, font=(font_tlt, 30))
button_login.pack(pady=20)

window.mainloop() 