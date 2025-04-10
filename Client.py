# little_alchemy_client.py
import socket
import threading
import dearpygui.dearpygui as dpg
import os
import json
from PIL import Image

HOST = 'localhost'
PORT = 9999

canvas_width, canvas_height = 800, 600
id_counter = 0
immagini = {}  # nome -> info
zaino = {}  # nome -> texture_path
combinazioni_scoperte = {}
ultima_combinazione = ""

ZAINO_FILE = "zaino.json"
STATO_FILE = "stato_gioco.json"
COMBO_FILE = "combinazioni_scoperte.json"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_server():
    try:
        client_socket.connect((HOST, PORT))
        print("🔌 Connesso al server.")
    except Exception as e:
        print("❌ Connessione fallita:", e)


def carica_texture(path):
    if not os.path.exists(path):
        return None, None
    image = Image.open(path)
    width, height = image.size
    with dpg.texture_registry():
        dpg.add_static_texture(width, height, image.tobytes(), tag=path)
    return path, (width, height)


def aggiungi_a_zaino(nome, texture_tag):
    if nome in zaino:
        return
    zaino[nome] = texture_tag
    with dpg.group(parent="zaino_container"):
        dpg.add_text(nome)
        dpg.add_image_button(texture_tag, width=40, height=40,
                             callback=lambda: crea_elemento(nome, texture_tag, posizione=(100, 100)))

def crea_elemento(nome, texture_tag, posizione=(50, 50)):
    global id_counter
    tag = f"elemento_{id_counter}"
    id_counter += 1
    dpg.add_image(texture_tag, tag=tag, pos=posizione)

    def drag_callback(sender, app_data):
        check_overlap(nome)

    dpg.set_item_drag_callback(tag, drag_callback)
    immagini[tag] = {
        "nome": nome,
        "tag": tag,
        "texture": texture_tag
    }
    aggiungi_a_zaino(nome, texture_tag)

def check_overlap(nome1):
    global ultima_combinazione
    pos1 = None
    tag1 = None
    for tag, dati in immagini.items():
        if dati["nome"] == nome1:
            tag1 = tag
            pos1 = dpg.get_item_pos(tag)
            break
    if not pos1:
        return

    for tag2, dati2 in immagini.items():
        if tag2 != tag1:
            pos2 = dpg.get_item_pos(tag2)
            if abs(pos1[0] - pos2[0]) < 50 and abs(pos1[1] - pos2[1]) < 50:
                nomi = sorted([nome1, dati2["nome"]])
                combinazione = "+".join(nomi)
                if combinazione in combinazioni_scoperte:
                    print("⚠️ Combinazione già fatta.")
                    return
                ultima_combinazione = combinazione
                print("🔗 Invia combinazione:", combinazione)
                client_socket.send(combinazione.encode('utf-8'))
                return


def listen_to_server():
    global ultima_combinazione
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            msg = data.decode('utf-8')
            print("📩 Dal server:", msg)
            if msg.startswith("NEW:"):
                _, nome, immagine = msg.split(":")
                if os.path.exists(immagine):
                    tex, _ = carica_texture(immagine)
                    crea_elemento(nome, tex, posizione=(200, 200))
                    combinazioni_scoperte[ultima_combinazione] = nome
        except:
            break


def salva_zaino():
    with open(ZAINO_FILE, "w") as f:
        json.dump(zaino, f)

def carica_zaino():
    if os.path.exists(ZAINO_FILE):
        with open(ZAINO_FILE, "r") as f:
            dati = json.load(f)
            for nome, path in dati.items():
                if os.path.exists(path):
                    tex, _ = carica_texture(path)
                    aggiungi_a_zaino(nome, tex)

def salva_stato_gioco():
    elementi = []
    for tag, dati in immagini.items():
        pos = dpg.get_item_pos(tag)
        elementi.append({
            "nome": dati["nome"],
            "texture": dati["texture"],
            "posizione": pos
        })
    with open(STATO_FILE, "w") as f:
        json.dump({"canvas": elementi, "zaino": zaino}, f)

def carica_stato_gioco():
    if os.path.exists(STATO_FILE):
        with open(STATO_FILE, "r") as f:
            stato = json.load(f)
            for nome, path in stato.get("zaino", {}).items():
                if os.path.exists(path):
                    tex, _ = carica_texture(path)
                    aggiungi_a_zaino(nome, tex)
            for elem in stato.get("canvas", []):
                if os.path.exists(elem["texture"]):
                    tex, _ = carica_texture(elem["texture"])
                    crea_elemento(elem["nome"], tex, posizione=tuple(elem["posizione"]))

def salva_combinazioni():
    with open(COMBO_FILE, "w") as f:
        json.dump(combinazioni_scoperte, f)

def carica_combinazioni():
    global combinazioni_scoperte
    if os.path.exists(COMBO_FILE):
        with open(COMBO_FILE, "r") as f:
            combinazioni_scoperte = json.load(f)

def setup_gui():
    dpg.create_context()
    dpg.create_viewport(title="Mini Little Alchemy", width=canvas_width + 200, height=canvas_height)
    dpg.setup_dearpygui()

    with dpg.window(label="Canvas", width=canvas_width, height=canvas_height):
        pass

    with dpg.window(label="Zaino", pos=(canvas_width, 0), width=200, height=canvas_height):
        dpg.add_text("Elementi scoperti:")
        with dpg.child_window(tag="zaino_container", width=180, height=canvas_height - 40):
            pass

    carica_zaino()
    carica_stato_gioco()
    carica_combinazioni()

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

def main():
    connect_to_server()
    threading.Thread(target=listen_to_server, daemon=True).start()
    try:
        setup_gui()
    finally:
        salva_zaino()
        salva_stato_gioco()
        salva_combinazioni()

if __name__ == '__main__':
    main()