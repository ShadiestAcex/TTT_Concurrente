import socket
import threading

user_db = {"Alfredo": "aaa",
        "JD": "bbb",
        "David": "ccc",
        "Itzel": "ddd",
        "Elias": "eee"}

logged_in_users = {}
active_games = {}  # Diccionario para rastrear juegos activos

lock = threading.Lock()

def handle_client(client_socket, username):
    global logged_in_users, active_games
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            # Solicitar lista de usuarios
            if data == "GET_USERS":
                with lock:
                    users_list = ','.join(logged_in_users.keys())
                    client_socket.send(f"USERS,{users_list}".encode('utf-8'))

            # Enviar desafío a un oponente
            elif data.startswith("CHALLENGE"):
                _, opponent = data.split(',')
                with lock:
                    if opponent in logged_in_users:
                        opponent_socket = logged_in_users[opponent]
                        try:
                            opponent_socket.send(f"CHALLENGE,{username}".encode('utf-8'))
                        except Exception as e:
                            print(f"Error enviando desafío a {opponent}: {e}")
                            client_socket.send("CHALLENGE_FAILED".encode('utf-8'))
                    else:
                        client_socket.send("OPPONENT_OFFLINE".encode('utf-8'))

            elif data.startswith("ACCEPT"):
                _, challenger = data.split(',')
                with lock:
                    if challenger in logged_in_users:
                        challenger_socket = logged_in_users[challenger]
                        try:
                            # Notificar al desafiante
                            challenger_socket.send(f"ACCEPT,{username}".encode('utf-8'))
                            # Crear una sesión de juego
                            game_id = f"{challenger}_{username}"
                            active_games[challenger] = game_id
                            active_games[username] = game_id
                        except Exception as e:
                            print(f"Error notificando al desafiante: {e}")
                            client_socket.send("CHALLENGER_OFFLINE".encode('utf-8'))



            # Rechazar desafío
            elif data.startswith("DECLINE"):
                _, challenger = data.split(',')
                with lock:
                    if challenger in logged_in_users:
                        challenger_socket = logged_in_users[challenger]
                        challenger_socket.send(f"DECLINE,{username}".encode('utf-8'))
                        print(f"{username} rechazó el desafío de {challenger}")

            # Movimiento en el juego
            elif data.startswith("MOVE"):
                _, position = data.split(',')
                game_id = active_games.get(username)
                if game_id:
                    players = game_id.split('_')
                    opponent = players[0] if players[1] == username else players[1]
                    with lock:
                        if opponent in logged_in_users:
                            try:
                                opponent_socket = logged_in_users[opponent]
                                opponent_socket.send(f"MOVE,{position}".encode('utf-8'))
                                client_socket.send("ACK".encode('utf-8'))
                                print(f"{username} realizó un movimiento en posición {position}")
                            except Exception as e:
                                print(f"Error enviando movimiento a {opponent}: {e}")
                                client_socket.send("ERROR_SENDING_MOVE".encode('utf-8'))
                        else:
                            client_socket.send("OPPONENT_DISCONNECTED".encode('utf-8'))
                else:
                    client_socket.send("NO_ACTIVE_GAME".encode('utf-8'))

            # Salida del cliente
            elif data == "EXIT":
                break

    except Exception as e:
        print(f"Error en cliente {username}: {e}")
    finally:
        with lock:
            if username in logged_in_users:
                del logged_in_users[username]
                print(f"{username} se ha desconectado.")
        client_socket.close()



def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(5)
    print("Servidor iniciado, esperando conexiones...")
    while True:
        client_socket, addr = server.accept()
        print(f"Conexión recibida de {addr}")
        # Manejar autenticación
        credentials = client_socket.recv(1024).decode('utf-8')
        if not credentials:
            client_socket.close()
            continue
        user, password = credentials.split(',')
        if user in user_db and user_db[user] == password:
            with lock:
                if user not in logged_in_users:
                    logged_in_users[user] = client_socket
            # Enviar lista de usuarios logueados
            users_list = ','.join(['Autenticación exitosa'] + list(logged_in_users.keys()))
            client_socket.send(users_list.encode('utf-8'))
            # Iniciar hilo para manejar al cliente
            client_handler = threading.Thread(target=handle_client, args=(client_socket, user))
            client_handler.start()
        else:
            client_socket.send("Error de autenticación".encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()