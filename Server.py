# ----- server.py -----
import socket
import threading
import json
import time
from game_logic import GameLogic

class GameServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # socket -> {"score": 0, "name": str}
        self.lock = threading.Lock()
        self.timer_started = False
        self.client_counter = 1

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Client connected from {addr}")
            with self.lock:
                name = f"Giocatore {self.client_counter}"
                self.clients[client_socket] = {"score": 0, "name": name}
                self.client_counter += 1
                if not self.timer_started:
                    self.timer_started = True
                    self.start_timer()

            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                self.process_data(client_socket, data)
        finally:
            with self.lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            client_socket.close()
            print("Client disconnected")

    def process_data(self, client_socket, data):
        message = json.loads(data)
        action = message.get("action")

        if action == "combine":
            elems = message["elements"]
            result, points = GameLogic().combine_elements(elems[0], elems[1])
            try:
                client_socket.send(json.dumps({
                    "action": "combination_result",
                    "result": result,
                    "points": points
                }).encode())
            except:
                pass
        elif action == "send_score":
            score = message.get("score", 0)
            with self.lock:
                if client_socket in self.clients:
                    self.clients[client_socket]["score"] = score

    def start_timer(self):
        def run_timer():
            total = 180 
            while total >= 0:
                mins, secs = divmod(total, 60)
                self.broadcast({
                    "action": "update_timer",
                    "minutes": mins,
                    "seconds": secs
                })
                time.sleep(1)
                total -= 1

            self.broadcast({"action": "game_over"})

            with self.lock:
                results = {info["name"]: info["score"] for info in self.clients.values()}
                winner = max(results.items(), key=lambda x: x[1])[0] if results else "Nessuno"
                final_message = {
                    "action": "final_results",
                    "results": results,
                    "winner": winner
                }
                self.broadcast(final_message)

        threading.Thread(target=run_timer, daemon=True).start()

    def broadcast(self, message):
        data = json.dumps(message).encode()
        with self.lock:
            for c in list(self.clients):
                try:
                    c.send(data)
                except:
                    del self.clients[c]

if __name__ == "__main__":
    GameServer().start_server()
