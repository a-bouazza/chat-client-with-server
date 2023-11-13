import socket
import threading

HOST = "192.168.1.191"
PORT = 3000


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


def receive_messages():
    while True:
        try:
            data = s.recv(1024)
            if not data:
                break
            message = data.decode().strip()
            if message.startswith("DELIVERY"):
                sender, message_content = message.split(" ", 2)[1:]
                print("\n" + f"{sender}: {message_content}")
                print("Enter a command : ")
                break
            else:
                print(f"{message}")
                print("Enter a command : ")
        except ConnectionResetError:
            print("Connection closed by server.")
            break


receive_thread = threading.Thread(target=receive_messages,args=(), daemon=True)
receive_thread.start()


while True:
    username = input("What is your username of choice: ")
    s.send(b"HELLO-FROM " + str.encode(username) + b"\n")

    data = s.recv(1024)

    split_data = data.decode()
    if split_data.startswith("HELLO"):
        print(f"{data.decode()} ")
        print("Enter a command : ")
        break
    elif split_data.startswith("IN-USE"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("Username is in use, please try again.")
    else:
        print("Server isn't responding, please try again.")
        break


def send_message(recipient, message_content):
    s.send(f"SEND {recipient} {message_content}\n".encode())
    response = s.recv(1024).decode()
    return response.strip()


receive_thread = threading.Thread(target=receive_messages,args=(), daemon=True)
receive_thread.start()


while True:
    try:
       
        command = input("")
        
        
        if command == "!quit":
            break
        elif command == "!who":
            s.send(b"LIST\n")
            response = s.recv(1024).decode()
            split_response = response.strip().split(" ")
            if split_response[0] == "LIST-OK":
                users = split_response[1:]
                print(f"Currently logged-in users: {', '.join(users)}")
            elif split_response[0] == "ERROR":
                print(f"Error retrieving user list: {response.strip()}")
            else:
                print("Invalid response.")
            continue
        elif command.startswith("@"):
            recipient, message_content = command[1:].split(" ", 1)
            s.send(f"SEND {recipient} {message_content}\n".encode())
            response = s.recv(1024).decode()
            print(f"{response}")
            if response.startswith("BAD-DEST-USER"):
                print("Not a Valid user")
                print("Enter a command : ")
        else:
            print("Invalid command.")
    except KeyboardInterrupt:
        s.send(b"QUIT\n")
        break
    except ConnectionResetError:
        print("Connection closed by server.")
        break
    