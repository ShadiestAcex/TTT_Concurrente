import socket
import threading
import tkinter as tk
from tkinter import messagebox

def open_waiting_room(logged_in_users, username, client_socket):
    waiting_room = tk.Toplevel(window)
    waiting_room.title("Sala de Espera")
    waiting_room.geometry("300x400")
    waiting_room.configure(bg="#D8BFD8")

    font_tlt = "Indie Flower"

    label_waiting = tk.Label(waiting_room, text="Sala de Espera", bg="#D8BFD8", fg="black", font=(font_tlt, 20))
    label_waiting.pack(pady=20)

    users_frame = tk.Frame(waiting_room, bg="#D8BFD8")
    users_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    def send_challenge(opponent):
        client_socket.send(f"CHALLENGE,{opponent}".encode('utf-8'))

    def update_user_list():
        try:
            client_socket.send("GET_USERS".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            if response.startswith("USERS"):
                _, users = response.split(',', 1)
                users = users.split(',')

                for widget in users_frame.winfo_children():
                    widget.destroy()

                for user in users:
                    if user != username:
                        frame_user = tk.Frame(users_frame, bg="#D8BFD8")
                        frame_user.pack(pady=5)
                        label_user = tk.Label(frame_user, text=user, bg="#D8BFD8", fg="black", font=(font_tlt, 15))
                        label_user.pack(side=tk.LEFT)
                        button_challenge = tk.Button(
                            frame_user,
                            text="Retar",
                            bg="#C99AF5",
                            font=(font_tlt, 12),
                            command=lambda u=user: send_challenge(u)
                        )
                        button_challenge.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error actualizando la lista de usuarios: {e}")

    def periodic_update():
        update_user_list()
        waiting_room.after(3000, periodic_update)

    periodic_update()

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
                        print("[DEBUG] Aceptando desafío. Este cliente NO es challenger.")
                        open_cat_window(username, challenger, client_socket, is_challenger=False)
                        return

                    else:
                        client_socket.send(f"DECLINE,{challenger}".encode('utf-8'))

                elif message.startswith("ACCEPT"):
                    _, opponent = message.split(',')
                    messagebox.showinfo("Desafío aceptado", f"{opponent} ha aceptado tu desafío.")
                    waiting_room.destroy()
                    print("[DEBUG] Oponente aceptó. Este cliente ES challenger.")
                    open_cat_window(username, opponent, client_socket, is_challenger=True)
                    return

                elif message.startswith("OPPONENT_DISCONNECTED"):
                    messagebox.showinfo("Información", "El oponente se desconectó.")

                elif message.startswith("DECLINE"):
                    _, decliner = message.split(',')
                    messagebox.showinfo("Información", f"{decliner} ha rechazado el desafío.")

            except Exception as e:
                print(f"Error en listen_for_messages: {e}")
                break

        print("Conexión cerrada.")

    threading.Thread(target=listen_for_messages, daemon=True).start()


def open_cat_window(username, opponent, client_socket, is_challenger):
    cat_window = tk.Toplevel(window)
    cat_window.title("Juego del Gato")
    cat_window.geometry("400x700")
    cat_window.configure(bg="#D8BFD8")

    font_tlt = "Indie Flower"

    current_turn = tk.StringVar()
    turn_symbol = tk.StringVar()
    game_over = tk.BooleanVar(value=False)
    board_lock = threading.Lock()
    current_score = "0-0"
    game_started = False  # Hasta recibir NEXT_ROUND no inicia el juego

    board = ['' for _ in range(9)]
    board_buttons = []

    print(f"[DEBUG] Entrando a open_cat_window() con is_challenger={is_challenger}, username={username}, opponent={opponent}")

    def regresar_menu():
        client_socket.send("EXIT".encode('utf-8'))
        cat_window.destroy()
        open_waiting_room([], username, client_socket)

    def button_click(i, j):
        # Si el juego no ha iniciado formalmente (game_started=False) o ya terminó (game_over), no se puede jugar
        if game_over.get() or not game_started:
            print("[DEBUG] Intento de movimiento cuando no está game_started o game_over=True, rechazado.")
            return
        with board_lock:
            if board[i*3+j] == '':
                board[i*3+j] = turn_symbol.get()
                board_buttons[i][j].config(text=turn_symbol.get(), state=tk.DISABLED)
                cat_window.update()

                print(f"[DEBUG] {username} hace un movimiento en {i},{j}. Turn symbol: {turn_symbol.get()}")
                client_socket.send(f"MOVE,{i*3+j}".encode('utf-8'))
                disable_board()

                winner = check_winner()
                if winner:
                    game_over.set(True)
                    round_winner = username if winner == turn_symbol.get() else opponent
                    client_socket.send(f"ROUND_WINNER,{round_winner}".encode('utf-8'))
                elif '' not in board:
                    game_over.set(True)
                    client_socket.send("ROUND_WINNER,Empate".encode('utf-8'))
                else:
                    # Ahora es turno del oponente
                    current_turn.set(f"Turno de: {opponent}")

    def disable_board():
        for row in board_buttons:
            for btn in row:
                btn.config(state=tk.DISABLED)
        print("[DEBUG] Tablero deshabilitado.")

    def enable_board():
        for i in range(9):
            if board[i] == '':
                board_buttons[i//3][i%3].config(state=tk.NORMAL)
        print("[DEBUG] Tablero habilitado para el jugador actual.")

    def check_winner():
        win_conditions = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a,b,c in win_conditions:
            if board[a] == board[b] == board[c] != '':
                return board[a]
        return None

    def reset_game():
        print("[DEBUG] reset_game() llamado. is_challenger:", is_challenger)
        for i in range(9):
            board[i] = ''
        for row in board_buttons:
            for btn in row:
                btn.config(text="", state=tk.NORMAL)

        game_over.set(False)
        if is_challenger:
            turn_symbol.set("X")
            current_turn.set(f"Turno de: {username}")
            enable_board()
        else:
            turn_symbol.set("O")
            current_turn.set(f"Turno de: {opponent}")
            disable_board()

        label_score.config(text=current_score)
        cat_window.update()

        if is_challenger:
            enable_board()
        else:
            disable_board()


    board_frame = tk.Frame(cat_window, bg="#D8BFD8")
    board_frame.pack(pady=20)

    for i in range(3):
        row = []
        for j in range(3):
            btn = tk.Button(
                board_frame,
                text="",
                font=(font_tlt, 20),
                width=5,
                height=2,
                state=tk.DISABLED,  # inicialmente deshabilitado hasta NEXT_ROUND
                command=lambda x=i, y=j: button_click(x, y)
            )
            btn.grid(row=i, column=j, padx=5, pady=5)
            row.append(btn)
        board_buttons.append(row)

    label_turn = tk.Label(cat_window, textvariable=current_turn, font=(font_tlt, 20), bg="#D8BFD8")
    label_turn.pack(pady=10)

    score_frame = tk.Frame(cat_window, bg="#D8BFD8")
    score_frame.pack(pady=10)

    label_player1 = tk.Label(score_frame, text=f"{username}", font=(font_tlt, 18), bg="#D8BFD8")
    label_player1.pack(side=tk.LEFT, padx=20)

    label_score = tk.Label(score_frame, text="0-0", font=(font_tlt, 18), bg="#D8BFD8")
    label_score.pack(side=tk.LEFT, padx=20)

    label_player2 = tk.Label(score_frame, text=f"{opponent}", font=(font_tlt, 18), bg="#D8BFD8")
    label_player2.pack(side=tk.LEFT, padx=20)

    action_frame = tk.Frame(cat_window, bg="#D8BFD8")
    action_frame.pack(pady=10)

    btn_regresar = tk.Button(action_frame, text="Regresar al Menú", bg="#C99AF5", font=(font_tlt, 14), command=regresar_menu)
    btn_regresar.pack(pady=10)

    def listen_for_moves():
        nonlocal game_started, current_score  # aseguramos que las asignaciones afecten a las variables externas
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    print("[DEBUG] Conexión cerrada desde listen_for_moves")
                    break

                if message.startswith("MOVE"):
                    _, position = message.split(',')
                    position = int(position)
                    symbol = 'O' if turn_symbol.get() == 'X' else 'X'
                    with board_lock:
                        board[position] = symbol
                        board_buttons[position//3][position%3].config(text=symbol, state=tk.DISABLED)
                        cat_window.update()
                    if not game_over.get():
                        current_turn.set(f"Turno de: {username}")
                        enable_board()

                elif message.startswith("SCORE"):
                    _, score = message.split(',')
                    label_score.config(text=score)
                    current_score = score
                    print("[DEBUG] SCORE recibido:", score)

                elif message.startswith("GAME_OVER"):
                    parts = message.split(',')
                    final_score = parts[1] if len(parts) > 1 else current_score
                    messagebox.showinfo("Juego terminado", f"El juego ha terminado. Marcador final: {final_score}")
                    cat_window.destroy()
                    open_waiting_room([], username, client_socket)
                    break

                elif message.startswith("NEXT_ROUND"):
                    print("[DEBUG] NEXT_ROUND recibido, iniciando ronda.")
                    game_started = True
                    reset_game()

                elif message == "OPPONENT_DISCONNECTED":
                    messagebox.showinfo("Información", "Tu oponente se desconectó.")
                    cat_window.destroy()
                    open_waiting_room([], username, client_socket)
                    break

                elif message == "NO_ACTIVE_GAME":
                    messagebox.showinfo("Información", "No hay juego activo.")
                    cat_window.destroy()
                    open_waiting_room([], username, client_socket)
                    break

                elif message == "ERROR_SENDING_MOVE":
                    messagebox.showerror("Error", "Error enviando el movimiento. Intente de nuevo.")

            except Exception as e:
                print(f"Error recibiendo movimientos: {e}")
                break

    threading.Thread(target=listen_for_moves, daemon=True).start()



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