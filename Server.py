# little_alchemy_server.py
import socket
import json
import os

HOST = 'localhost'
PORT = 9999

COMBINAZIONI_FILE = "combinazioni_server.json"

def carica_combinazioni():
    if os.path.exists(COMBINAZIONI_FILE):
        with open(COMBINAZIONI_FILE, "r") as f:
            return json.load(f)
    return {}

def salva_combinazioni(dati):
    with open(COMBINAZIONI_FILE, "w") as f:
        json.dump(dati, f)

combinazioni = carica_combinazioni()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"🖥️ Server in ascolto su {HOST}:{PORT}")

client_socket, addr = server_socket.accept()
print(f"✅ Client connesso da {addr}")

try:
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        msg = data.decode('utf-8')
        print("Ricevuto:", msg)

        if msg in combinazioni:
            nome, immagine = combinazioni[msg]
            risposta = f"NEW:{nome}:{immagine}"
        else:
            risposta = "❌ Combinazione non valida."
        client_socket.send(risposta.encode('utf-8'))
finally:
    client_socket.close()
    server_socket.close()
    salva_combinazioni(combinazioni)
