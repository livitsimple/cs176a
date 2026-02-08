import socket
import struct
import sys

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
    return data

def game_pack_proc(client):
    header = recv_exact(client, 2)
    word_len, num_incorrect = struct.unpack("!BB", header)

    msg = recv_exact(client, word_len + num_incorrect)

    word = msg[:word_len].decode()
    incorrect = msg[word_len:].decode()

    print(word)
    print("Incorrect Guesses: " + incorrect)

    

def cntrl_pack_proc(client, msg_len):
    gm_cntrl = recv_exact(client, msg_len).decode()
    print(gm_cntrl)
    return

def tcp_client(ip, port):
    """
    TCP Client for hangman game.
    
    Args:
        ip: server IP address
        port: server port
        s: string to send
    
    Output:
        Print each response line as: "From server: <line>"
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))
    
    confirmation = input("Ready to start game? (y/n):")

    if confirmation == "n":
        client.close()
    else:
        header_0 = struct.pack("!B", 0)
        client.send(header_0)


    while True:
        byte_1 = struct.unpack("!B", recv_exact(client, 1))[0]

        if byte_1 > 0:
            cntrl_pack_proc(client, byte_1)
            break

        game_pack_proc(client)

        valid_input = False

        while not valid_input:
            guess = input("Letter to guess:")
            if len(guess) != 1 or not guess.isalpha():
                print("Error! Please guess one letter.")
                continue
            valid_input = True

        client.sendall(b"1" + guess.lower().encode())

    for _ in range(2):
        byte_1 = struct.unpack("!B", recv_exact(client, 1))[0]
        cntrl_pack_proc(client, byte_1)
    
    client.close()

tcp_client(sys.argv[1], int(sys.argv[2]))
