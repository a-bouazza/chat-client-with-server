import socket
import threading

HOST = "192.168.1.191"
PORT = 3000
MAX_CLIENTS = 64

def handle_client(conn, addr):
    print("Connected by", addr)

    if len(connections) >= MAX_CLIENTS:
        conn.send(b"BUSY\n")
        conn.close()
        print("Maximum number of clients reached.")
        return

    username = conn.recv(1024).decode().strip()
    username = username.replace("HELLO-FROM ", "")
    print(f"{username} has connected.")

    if username in registered_users:
        conn.send(b"IN-USE")
        conn.close()
        return
    else:
        registered_users[username] = conn
        print(f"{username} has been added to registered_users.")
        conn.send(b"HELLO")

    def send_message(sender, recipient, message_content):
        if recipient in registered_users:
            recipient_conn = registered_users[recipient]
            recipient_conn.send(f"DELIVERY {sender} {message_content}\n".encode())
            conn.send(b"SEND-OK")
        else:
            conn.send(b"BAD-DEST-USER")

    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            if data == "LIST":
                user_list = " ".join(sorted(list(registered_users.keys())))
                conn.send(f"LIST-OK {user_list}\n".encode())
            elif data.startswith("SEND"):
                _, recipient, message_content = data.split(" ", 2)
                send_message(username, recipient, message_content)
            elif data == "QUIT":
                break
            else:
                conn.send(b"ERROR Invalid command")
        except ConnectionResetError:
            break

    del registered_users[username]
    conn.close()
    print("Connection closed by", addr)

registered_users = {}
connections = []

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    while True:
        conn, addr = s.accept()
        connections.append((addr[0], conn))
        threading.Thread(target=handle_client, args=(conn, addr)).start()