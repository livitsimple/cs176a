import socket
import threading
import struct
import threading
import random
import sys

HOST = "127.0.0.1"
CLIENT_MAX = 3
INCORRECT_MAX = 6
active_clients = []
lock = threading.Lock()

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
    return data

def create_cntrl_packet(message):
    encoded = message.encode()
    length = len(encoded)

    header = struct.pack("!B", length)
    return header + encoded

def create_game_packet(correct, incorrect):
    msg_flag = 0
    word_len = len(correct)
    num_incorrect = len(incorrect)

    header = struct.pack("!BBB", msg_flag, word_len, num_incorrect)

    data = correct.encode() + incorrect.encode()

    return header + data

def end_game(win, game_word, client_socket):
    messages = []

    messages.append(f"The word was {game_word}")

    if win:
        messages.append("You Win!")
    else:
        messages.append("You Lose!")

    messages.append("Game Over!")

    for msg in messages:
        packet = create_cntrl_packet(msg)
        client_socket.sendall(packet)


def client_handler(client_socket, client_address):
    incorrect = ""

    try:
        start_len = struct.unpack("!B", recv_exact(client_socket, 1))[0]
    except ConnectionError:
        return
    
    if start_len != 0:
        return
    
    with open("hangman_words.txt", "r") as f:
        words = [line.strip() for line in f if line.strip()]
        numWords = len(words)
        i = random.randrange(0, numWords)
        game_word = words[i]
    
    correct = ["_" for _ in game_word]

    packet = create_game_packet("".join(correct), incorrect)
    client_socket.sendall(packet)

    

    while True:

        try:
            msg_len = struct.unpack("!B", recv_exact(client_socket, 1))[0]
        except ConnectionError:
            break

        if msg_len == 0:
            continue

        try:
            guess_bytes = recv_exact(client_socket, msg_len)
        except ConnectionError:
            break

        guess = guess_bytes.decode()

        if len(guess) != 1 or not guess.isalpha():
            packet = create_game_packet("".join(correct), incorrect)
            client_socket.sendall(packet)
            continue

        guess = guess.lower()


        if guess in game_word:
            appear_loc = [i for i, ch in enumerate(game_word) if ch == guess]

            for loc in appear_loc:
                correct[loc] = guess
        else:
            if guess not in incorrect:
                incorrect += guess
        
        if len(incorrect) >= INCORRECT_MAX:
            end_game(False, game_word, client_socket)
            break
        elif "_" not in correct:
            end_game(True, game_word, client_socket)
            break

        packet = create_game_packet("".join(correct), incorrect)
        client_socket.sendall(packet)
    
    with lock:
        if client_socket in active_clients:
            active_clients.remove(client_socket)

    client_socket.close()


def tcp_server(port):
    """    
    Args:
        port: port number to listen on
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, port))
    server.listen(2)
    
    while True:
        client_socket, client_address = server.accept()

        with lock:
            if len(active_clients) >= CLIENT_MAX:
                overload = "server-overloaded"
                client_socket.sendall(create_cntrl_packet(overload))
                client_socket.close()
                continue
            active_clients.append(client_socket)

        t = threading.Thread(target=client_handler, args=(client_socket, client_address), daemon=True)
        
        t.start()

tcp_server(int(sys.argv[1]))
