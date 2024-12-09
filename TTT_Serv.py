import socket
import threading
import time

user_db = {
    "Alfredo": "aaa",
    "JD": "bbb",
    "David": "ccc",
    "Itzel": "ddd",
    "Elias": "eee"
}

logged_in_users = {}
active_games = {}  # user -> game_id
scores = {}  # {username: puntos}

lock = threading.Lock()

def handle_client(client_socket, username):
    global logged_in_users, active_games, scores
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            if message.startswith("CHALLENGE"):
                _, opponent = message.split(',')
                with lock:
                    if opponent in logged_in_users:
                        opponent_socket = logged_in_users[opponent]
                        opponent_socket.send(f"CHALLENGE,{username}".encode('utf-8'))
                    else:
                        client_socket.send("ERROR,Opponent not available".encode('utf-8'))

            elif message.startswith("ACCEPT"):
                _, challenger = message.split(',')
                with lock:
                    if challenger in logged_in_users:
                        challenger_socket = logged_in_users[challenger]
                        game_id = f"{challenger}_vs_{username}"
                        active_games[challenger] = game_id
                        active_games[username] = game_id
                        scores[game_id] = {challenger: 0, username: 0}
                        challenger_socket.send(f"NEXT_ROUND".encode('utf-8'))
                        client_socket.send(f"NEXT_ROUND".encode('utf-8'))
                    else:
                        client_socket.send("ERROR,Challenger not available".encode('utf-8'))

            elif message.startswith("MOVE"):
                _, position = message.split(',')
                game_id = active_games[username]
                with lock:
                    for player in active_games:
                        if active_games[player] == game_id and player != username:
                            logged_in_users[player].send(f"MOVE,{position}".encode('utf-8'))
                            break

            elif message.startswith("ROUND_WINNER"):
                _, winner = message.split(',')
                game_id = active_games[username]
                with lock:
                    if winner != "Empate":
                        scores[game_id][winner] += 1
                    for player in active_games:
                        if active_games[player] == game_id:
                            logged_in_users[player].send(f"SCORE,{scores[game_id][player]}-{scores[game_id][player]}".encode('utf-8'))
                            logged_in_users[player].send("NEXT_ROUND".encode('utf-8'))

            elif message == "EXIT":
                break

            elif message == "GET_USERS":
                with lock:
                    users_list = ",".join(logged_in_users.keys())
                    client_socket.send(f"USERS,{users_list}".encode('utf-8'))

    except Exception as e:
        print(f"Error manejando cliente {username}: {e}")
    finally:
        with lock:
            if username in logged_in_users:
                del logged_in_users[username]
            if username in active_games:
                del active_games[username]
        client_socket.close()

def authenticate_client(client_socket):
    try:
        credentials = client_socket.recv(1024).decode('utf-8')
        username, password = credentials.split(',')
        if username in user_db and user_db[username] == password:
            with lock:
                logged_in_users[username] = client_socket
            client_socket.send(f"Autenticación exitosa,{','.join(logged_in_users.keys())}".encode('utf-8'))
            handle_client(client_socket, username)
        else:
            client_socket.send("Error de autenticación".encode('utf-8'))
            client_socket.close()
    except Exception as e:
        print(f"Error autenticando cliente: {e}")
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))  # Escuchar en todas las interfaces de red
    server.listen(5)
    print("Servidor iniciado, esperando conexiones...")
    while True:
        client_socket, addr = server.accept()
        print(f"Conexión recibida de {addr}")
        threading.Thread(target=authenticate_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()