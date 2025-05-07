# 🧪 Mixet

Un gioco multiplayer ispirato a *Little Alchemy*, sviluppato in Python. Ogni giocatore riceve elementi base e può combinarli per scoprire nuovi oggetti. Il gioco è interamente gestito con **socket TCP** e ha un'interfaccia realizzata con **DearPyGui**.

---

## 🔧 Tecnologie utilizzate

- **Python 3.10+**
- **DearPyGui** per l'interfaccia grafica
- **Socket TCP** per la comunicazione client-server
- **Threading** per la gestione asincrona
- **JSON** per la serializzazione dei messaggi

---

## 🎮 Funzionalità principali

- Multiplayer asincrono basato su socket
- Inventario separato per ogni client
- Punteggio individuale aggiornato in tempo reale
- Timer di gioco condiviso tra tutti i client
- Sistema di scoperta degli oggetti (senza duplicati)
- Riepilogo finale del punteggio e degli oggetti scoperti

---

## 🗂️ Struttura del progetto
alchemy-multiplayer/
├── client.py # Client del gioco, GUI + logica di interazione
├── server.py # Server TCP che gestisce i client e il timer
├── game_logic.py # Gestione combinazioni e punteggio
├── timer.py # Timer condiviso tra i client
├── README.md # Questo file

yaml
Copia
Modifica

---

## 🚀 Come eseguirlo

### 1. Clona il repository

```bash
git clone https://github.com/tuo-username/alchemy-multiplayer.git
cd alchemy-multiplayer
2. Installa le dipendenze
bash
Copia
Modifica
pip install dearpygui
3. Avvia il server
bash
Copia
Modifica
python server.py
4. Avvia uno o più client (in terminali separati)
bash
Copia
Modifica
python client.py 5000
🔁 Assicurati che la porta sia la stessa sia nel client che nel server.
