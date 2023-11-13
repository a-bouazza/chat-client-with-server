import socket
import threading

HOST = "192.168.1.191"
PORT = 3000

def handle_client(conn, addr):
    print("Connected by", addr)

    username = conn.recv(1024).decode()
    username = username.replace("HELLO-FROM ", "")
    print(f"{username} has connected.")
    if username in registered_users:
        conn.send(b"EXIST")
    else:
        registered_users.add(username)
        print(f"{username} has been added to registered_users.")
        conn.send(b"OK")

    while True:
        data = conn.recv(1024).decode()
        print(f"Received data: {data}")
        if data == "!who":
            user_list = ", ".join(sorted(list(registered_users)))
            conn.send(user_list.encode())
        elif data == "!quit":
            break
        elif data.startswith("@"):
            recipient, message = data[1:].split(" ", 1)
            print(f"Recipient: {recipient}, Message: {message}")
            if recipient in registered_users:
                conn.send(f"{username}: {message}".encode())
                recipient_conn = None
                for c in connections:
                    if c[0] == recipient:
                        recipient_conn = c[1]
                        break
                if recipient_conn:
                    recipient_conn.send(f"{username}: {message}".encode())
            else:
                conn.send(f"Error: User {recipient} is not registered".encode())
        else:
            conn.send(data.encode())

    registered_users.remove(username)
    conn.close()
    print("Connection closed by", addr)

registered_users = set()
connections = []

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    while True:
        conn, addr = s.accept()
        connections.append((addr[0], conn))
        threading.Thread(target=handle_client, args=(conn, addr)).start()