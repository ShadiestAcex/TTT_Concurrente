import socket
import threading
import time

user_db = {"Alfredo": "aaa",
           "JD": "bbb",
           "David": "ccc",
           "Itzel": "ddd",
           "Elias": "eee"}

logged_in_users = {}
active_games = {}  # user -> game_id
scores = {}  # {username: puntos}

lock = threading.Lock()

def handle_client(client_socket, username):
    global logged_in_users, active_games, scores
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            if data == "GET_USERS":
                with lock:
                    users_list = ','.join(logged_in_users.keys())
                client_socket.send(f"USERS,{users_list}".encode('utf-8'))

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
                            challenger_socket.send(f"ACCEPT,{username}".encode('utf-8'))
                            game_id = f"{challenger}_{username}"
                            active_games[challenger] = game_id
                            active_games[username] = game_id

                            opponent = challenger
                            if username not in scores:
                                scores[username] = 0
                            if opponent not in scores:
                                scores[opponent] = 0

                            # Enviar SCORE inicial
                            challenger_socket.send(f"SCORE,{scores[challenger]}-{scores[username]}".encode('utf-8'))
                            client_socket.send(f"SCORE,{scores[username]}-{scores[challenger]}".encode('utf-8'))

                            # Pausa antes de NEXT_ROUND para dar tiempo a cliente
                            time.sleep(0.5)

                            # Primer NEXT_ROUND
                            challenger_socket.send("NEXT_ROUND".encode('utf-8'))
                            client_socket.send("NEXT_ROUND".encode('utf-8'))

                        except Exception as e:
                            print(f"Error notificando al desafiante: {e}")
                            client_socket.send("CHALLENGER_OFFLINE".encode('utf-8'))

            elif data.startswith("DECLINE"):
                _, challenger = data.split(',')
                with lock:
                    if challenger in logged_in_users:
                        challenger_socket = logged_in_users[challenger]
                        challenger_socket.send(f"DECLINE,{username}".encode('utf-8'))
                        print(f"{username} rechazó el desafío de {challenger}")

            elif data.startswith("MOVE"):
                _, position = data.split(',')
                with lock:
                    game_id = active_games.get(username)
                    if game_id:
                        p1, p2 = game_id.split('_')
                        opponent = p1 if p2 == username else p2
                        if opponent in logged_in_users:
                            opponent_socket = logged_in_users[opponent]
                            try:
                                print(f"[DEBUG] Enviando movimiento {position} a {opponent}.")
                                opponent_socket.send(f"MOVE,{position}".encode('utf-8'))
                                client_socket.send("ACK".encode('utf-8'))
                                print(f"[DEBUG] {username} realizó un movimiento en posición {position}")
                            except Exception as e:
                                print(f"[ERROR] Error enviando movimiento a {opponent}: {e}")
                                client_socket.send("ERROR_SENDING_MOVE".encode('utf-8'))
                        else:
                            client_socket.send("OPPONENT_DISCONNECTED".encode('utf-8'))
                            if opponent in active_games:
                                del active_games[opponent]
                            if username in active_games:
                                del active_games[username]
                    else:
                        client_socket.send("NO_ACTIVE_GAME".encode('utf-8'))

            elif data.startswith("ROUND_WINNER"):
                _, winner = data.split(',')
                with lock:
                    game_id = active_games.get(username)
                    if game_id:
                        p1, p2 = game_id.split('_')

                        if winner != "Empate":
                            if winner in scores:
                                scores[winner] += 1
                            else:
                                scores[winner] = 1

                        if p1 in logged_in_users and p2 in logged_in_users:
                            p1_socket = logged_in_users[p1]
                            p2_socket = logged_in_users[p2]

                            if scores[p1] == 2 or scores[p2] == 2:
                                p1_socket.send(f"GAME_OVER,{scores[p1]}-{scores[p2]}".encode('utf-8'))
                                p2_socket.send(f"GAME_OVER,{scores[p2]}-{scores[p1]}".encode('utf-8'))
                                del active_games[p1]
                                del active_games[p2]
                                print(f"Juego terminado. {p1}: {scores[p1]} vs {p2}: {scores[p2]}")
                            else:
                                p1_socket.send(f"SCORE,{scores[p1]}-{scores[p2]}".encode('utf-8'))
                                p2_socket.send(f"SCORE,{scores[p2]}-{scores[p1]}".encode('utf-8'))

                                time.sleep(0.5)  # Pausa antes de NEXT_ROUND
                                p1_socket.send("NEXT_ROUND".encode('utf-8'))
                                p2_socket.send("NEXT_ROUND".encode('utf-8'))
                        else:
                            if p1 in active_games:
                                del active_games[p1]
                            if p2 in active_games:
                                del active_games[p2]

            elif data == "GAME_OVER":
                with lock:
                    game_id = active_games.get(username)
                    if game_id:
                        p1, p2 = game_id.split('_')
                        opponent = p1 if p2 == username else p2
                        if opponent in logged_in_users:
                            try:
                                opponent_socket = logged_in_users[opponent]
                                opponent_socket.send("GAME_OVER".encode('utf-8'))
                            except Exception as e:
                                print(f"Error notificando GAME_OVER: {e}")
                        if username in active_games:
                            del active_games[username]
                        if opponent in active_games:
                            del active_games[opponent]
                        print(f"Juego {game_id} terminado por {username}.")

            elif data == "EXIT":
                with lock:
                    if username in active_games:
                        game_id = active_games[username]
                        p1, p2 = game_id.split('_')
                        opponent = p1 if p2 == username else p2
                        if opponent in logged_in_users:
                            opponent_socket = logged_in_users[opponent]
                            opponent_socket.send("OPPONENT_DISCONNECTED".encode('utf-8'))
                        if opponent in active_games:
                            del active_games[opponent]
                        del active_games[username]
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
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 9999))
    server.listen(5)
    print("Servidor iniciado, esperando conexiones...")
    while True:
        client_socket, addr = server.accept()
        print(f"Conexión recibida de {addr}")
        credentials = client_socket.recv(1024).decode('utf-8')
        if not credentials:
            client_socket.close()
            continue
        user, password = credentials.split(',')
        if user in user_db and user_db[user] == password:
            with lock:
                if user not in logged_in_users:
                    logged_in_users[user] = client_socket
            with lock:
                users_list = ','.join(['Autenticación exitosa'] + list(logged_in_users.keys()))
            client_socket.send(users_list.encode('utf-8'))
            client_handler = threading.Thread(target=handle_client, args=(client_socket, user))
            client_handler.start()
        else:
            client_socket.send("Error de autenticación".encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("Servidor detenido por el usuario.")