import socket
import threading
import hashlib

HOST = "143.47.184.219"
PORT = 5382

sent_messages = {}

sent_messages_lock = threading.Lock()

sequence_number = 0

acknowledgment_counter = 0

all_acknowledged_event = threading.Event()

error_detected_event = threading.Event()

def calculate_checksum(message):
    md5_hash = hashlib.md5()
    md5_hash.update(message.encode())
    return md5_hash.digest()

def send_message(message, sock):
    global sequence_number
    checksum = calculate_checksum(message)
    sequence_number += 1
    packet = f"{sequence_number}:{checksum.hex()}:{message}"
    sent_messages[sequence_number] = False
    sock.sendto(packet.encode(), (HOST, PORT))


def receive_acknowledgments(sock):
    global acknowledgment_counter
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            acknowledgment = int(data.decode())
            with sent_messages_lock:
                if acknowledgment in sent_messages:
                    sent_messages[acknowledgment] = True
                    acknowledgment_counter += 1
                    if acknowledgment_counter == len(sent_messages):
                        all_acknowledged_event.set()
        except ConnectionResetError:
            error_detected_event.set()
            break


def receive_messages(sock):
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            sequence_number, checksum, message = data.decode().split(":", 2)
            if calculate_checksum(message) == checksum.encode():
                print(f"Received: {message}")
            else:
                print("Error detected in message.")
        except ConnectionResetError:
            error_detected_event.set()
            break


def run_chat_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.settimeout(10)

    ack_thread = threading.Thread(target=receive_acknowledgments, args=(sock,), daemon=True)
    ack_thread.start()

    receive_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receive_thread.start()

    while True:
        try:
            username = input("What is your username of choice: ")
            send_message(f"HELLO-FROM {username}", sock)
            all_acknowledged_event.wait(2)
            if all_acknowledged_event.is_set():
                all_acknowledged_event.clear()
                if error_detected_event.is_set():
                    error_detected_event.clear()
                    print("Connection closed by server.")
                    break
                break
            else:
                print("Server isn't responding, please try again.")
        except KeyboardInterrupt:
            send_message("QUIT", sock)
            all_acknowledged_event.wait(2)
            if all_acknowledged_event.is_set():
                all_acknowledged_event.clear()
                break
            else:
                print("Error occurred while quitting.")
                break

    while True:
        try:
            command = input("Enter a command: ")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if command == "!quit":
                send_message("QUIT", sock)
                all_acknowledged_event.wait(2)
                if all_acknowledged_event.is_set():
                    all_acknowledged_event.clear()
                    break
                else:
                    print("Error occurred while quitting.")
                    break
            elif command == "!who":
                send_message("LIST", sock)
                all_acknowledged_event.wait(2)
                if all_acknowledged_event.is_set():
                    all_acknowledged_event.clear()
                    all_acknowledged_event.wait(2)
                    if all_acknowledged_event.is_set():
                        all_acknowledged_event.clear()
                        if error_detected_event.is_set():
                            error_detected_event.clear()
                            print("Connection closed by server.")
                            break
                    else:
                        print("Error occurred while retrieving user list.")
                else:
                    print("Error occurred while sending command.")
            elif command.startswith("@"):
                recipient, message_content = command[1:].split(" ", 1)
                send_message(f"SEND {recipient} {message_content}", sock)
                all_acknowledged_event.wait(2)
                if all_acknowledged_event.is_set():
                    all_acknowledged_event.clear()
                    if error_detected_event.is_set():
                        error_detected_event.clear()
                        print("Connection closed by server.")
                        break
                else:
                    print("Error occurred while sending message.")
            else:
                print("Invalid command.")
            sock.close()
        except KeyboardInterrupt:
            send_message("QUIT", sock)
            all_acknowledged_event.wait(2)
            if all_acknowledged_event.is_set():
                all_acknowledged_event.clear()
                break
            else:
                print("Error occurred while quitting.")
                break
        except ConnectionResetError:
            print("Connection closed by server.")
            break

    sock.close()

run_chat_client()
