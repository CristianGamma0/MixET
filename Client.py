# ----- client.py -----
from dearpygui.dearpygui import *
import socket
import threading
import json
import time
import os

INVENTORY_FILE = 'inventory.json'
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

def load_inventory(default):
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(default, f)
    return default

class GameClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.game_over_flag = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        default_inv = ["Fuoco", "Acqua", "Terra", "Aria"]
        self.inventory = load_inventory(default_inv)
        self.discovered = set()
        self.dropped_elements = []
        self.timer_tag = None
        self.results_area = None
        self.inv_child = None
        self.score = 0
        self.score_tag = None

    def save_inventory(self):
        try:
            with open(INVENTORY_FILE, 'w') as f:
                json.dump(self.inventory, f)
        except Exception as e:
            print(f"Errore salvataggio inventory: {e}")

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.host, self.port))
            threading.Thread(target=self.listen_to_server, daemon=True).start()
        except Exception as e:
            print(f"Errore nella connessione al server: {e}")

    def listen_to_server(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data: break
                message = json.loads(data)
                threading.Thread(target=self.process_server_message, args=(message,), daemon=True).start()
            except Exception as e:
                print(f"Errore nella ricezione: {e}")
                break

    def process_server_message(self, message):
        action = message.get("action")
        if action == "game_over":
            self.show_game_over_screen()
        elif action == "combination_result":
            delete_item(self.results_area, children_only=True)
            result = message.get('result')
            points = message.get('points', 0)
            if result in self.discovered:
                add_text(f"Oggetto '{result}' gia' scoperto! Nessun punto assegnato.", parent=self.results_area, color=[255,165,0])
            else:
                self.discovered.add(result)
                self.score += points
                set_item_pos(self.score_tag, [WINDOW_WIDTH-200, 10])
                set_value(self.score_tag, f"Punteggio: {self.score}")
                add_text(f"Nuovo oggetto: {result} (+{points} punti)", parent=self.results_area, color=[0,255,0])
                if result not in self.inventory:
                    self.inventory.append(result)
                    self.save_inventory()
                    btn = add_button(label=result, parent=self.inv_child, tag=f"btn_{result}_{int(time.time())}")
                    with drag_payload(parent=btn, payload_type="ITEM", drag_data=result):
                        add_text(result)
        elif action == "update_timer":
            mins = message.get("minutes")
            secs = message.get("seconds")
            if does_item_exist(self.timer_tag):
                set_value(self.timer_tag, f"Timer: {mins}:{secs:02}")
        elif action == "final_results":
            results = message.get("results", {})
            winner = message.get("winner")
            self.display_final_results(results, winner)

    def start_game_ui(self):
        def on_drop(sender, app_data):
            drag_data = app_data
            self.dropped_elements.append(drag_data)
            add_text(f"Dropped: {drag_data}", parent="drop_child")
            if len(self.dropped_elements) == 2:
                delete_item("drop_child", children_only=True)
                self.send_to_server({"action":"combine","elements":self.dropped_elements})
                self.dropped_elements.clear()

        create_context()
        with window(tag="game_window", label="Game Screen", width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
            threading.Thread(target=self.monitor_game_over_flag, daemon=True).start()
            set_primary_window("game_window", True)
            self.timer_tag = add_text("Timer: 3:00")
            self.score_tag = add_text(f"Punteggio: {self.score}")
            set_item_pos(self.score_tag, [WINDOW_WIDTH-200, 10])
            add_separator()
            self.results_area = add_child_window(width=400, height=100, border=True)
            add_text("Risultati:", parent=self.results_area)
            add_separator()
            add_text("Inventory:")
            self.inv_child = add_child_window(width=350, height=200, border=True)
            for elem in self.inventory:
                btn = add_button(label=elem, parent=self.inv_child, tag=f"btn_{elem}")
                with drag_payload(parent=btn, payload_type="ITEM", drag_data=elem):
                    add_text(elem)
            group(horizontal=True)
            self.speciali = add_text("Combinazioni speciali (5 punti):")
            with child_window(tag="names_child", width= WINDOW_WIDTH - 400, height=150, border=False):
                add_text("Andrea Pollini")
                add_text("Sottile")
                add_text("Steve")
                add_text("Patrick")
                add_text("Yamal")
            with child_window(tag="names_child2", width= WINDOW_WIDTH - 400, height=150, border=False):
                add_text("Lirili Larila")
                add_text("Fungo Porcino")
                add_text("Mortaio di Clash Royale")
                add_text("Minato Namikaze")
                add_text("Eva 0-1")
            set_item_pos(self.speciali, [WINDOW_WIDTH - 350, 150])
            set_item_pos("names_child", [WINDOW_WIDTH - 400, 200])
            set_item_pos("names_child2", [WINDOW_WIDTH - 200, 200])
            add_separator()
            add_text("Drop Area:")
            with child_window(tag="drop_child", width=350, height=300, border=True,
                       payload_type="ITEM", drop_callback=on_drop):
                add_text("Rilascia qui")

        create_viewport(title="Game Client", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        setup_dearpygui()
        show_viewport()
        start_dearpygui()
        destroy_context()

    def monitor_game_over_flag(self):
        # Controlla continuamente il flag finché non è attivo
        while not self.game_over_flag:
            time.sleep(0.5)

        # Quando il gioco finisce, chiama la funzione per mostrare la schermata di fine partita
        set_item_label("score_tag", f"Gioco Terminato - Punteggio finale: {self.score}")
        self.show_game_over_screen()
    
    def show_game_over_screen(self):
        # Elimina la finestra di gioco
        if does_item_exist("game_window"):
            delete_item("game_window")

        # Crea la finestra finale con il punteggio e gli oggetti scoperti
        with window(tag="end_screen", label="Game Over", width=400, height=300):
            add_text("Partita terminata!")
            add_separator()
            add_text(f"Punteggio finale: {self.score}")
            add_text("Oggetti scoperti:")
            for obj in sorted(self.discovered):
                add_text(f"{obj}")
            add_spacing(count=2)
            add_button(label="Esci", callback=lambda: stop_dearpygui())

    def send_to_server(self, message):
        try:
            self.client_socket.send(json.dumps(message).encode())
        except Exception as e:
            print(f"Errore invio: {e}")

    def create_gui(self):
        self.connect_to_server()
        self.start_game_ui()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python client.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    client = GameClient(host='localhost', port=port)
    client.create_gui()
