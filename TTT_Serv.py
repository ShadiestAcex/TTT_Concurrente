import socket
import threading

user_db = {"Alfredo": "aaa",
        "JD": "bbb",
        "David": "ccc",
        "Itzel": "ddd",
        "Elias": "eee"}

def handle_client(client_socket):
    while True:
        try:
            credentials = client_socket.recv(1024).decode('utf-8')
            if not credentials:
                break
            user, password = credentials.split(',')
            if user in user_db and user_db[user] == password:
                client_socket.send("Autenticación exitosa".encode('utf-8'))
            else:
                client_socket.send("Error de autenticación".encode('utf-8'))
        except():
            break
    client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(5)
    print("Servidor iniciado, esperando conexiones...")
    while True:
        client_socket, addr = server.accept()
        print (f"Conexión recibida de {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()