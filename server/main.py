import socket
import threading
import json
from protocols import Protocols
from room import Room
import time
from db import DB


class Server:
    def __init__(self, host="127.0.0.1", port=55555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

        self.client_names = {}
        self.opponent = {}
        self.rooms = {}
        self.waiting_for_pair = None

        self.db = DB()

    def handle_connect(self, client):
        while True:
            self.send(Protocols.Response.NICKNAME, None, client)
            message = json.loads(client.recv(1024).decode("ascii"))
            r_type = message.get("type")
            nickname = message.get("data")

            if r_type == Protocols.Request.NICKNAME:
                self.client_names[client] = nickname
            else:
                continue

            if not self.waiting_for_pair:
                self.waiting_for_pair = client
                print("waiting for a room")
            else:
                self.create_room(client)
            
            break

    def create_room(self, client):
        print("Creating room.")
        room = Room(client, self.waiting_for_pair)
        self.opponent[client] = self.waiting_for_pair
        self.opponent[self.waiting_for_pair] = client

        self.send(Protocols.Response.OPPONENT, self.get_client_data(client), self.waiting_for_pair)
        self.send(Protocols.Response.OPPONENT, self.get_client_data(self.waiting_for_pair), client)

        self.rooms[client] = room
        self.rooms[self.waiting_for_pair] = room
        self.waiting_for_pair = None

    def get_client_data(self, client):
        name = self.client_names[client]
        data = self.db.get_user_stats(name)
        return {"name": name, "wins": data["wins"], "losses": data["losses"]}

    def wait_for_room(self, client):
        while True:
            room = self.rooms.get(client)
            opponent = self.opponent.get(client)

            if room and opponent:
                self.send(Protocols.Response.QUESTIONS, room.questions, client)
                time.sleep(1)
                self.send(Protocols.Response.START, None, client)
                break

    def handle(self, client):
        self.handle_connect(client)
        self.wait_for_room(client)

        while True:
            try:
                data = client.recv(1024).decode("ascii")
                if not data:
                    break
                message = json.loads(data)
                self.handle_receive(message, client)
            except:
                break
        
        self.send_to_opponent(Protocols.Response.OPPONENT_LEFT, None, client)
        self.disconnect(client)

    def disconnect(self, client):
        opponent = self.opponent.get(client)
        if opponent in self.opponent:
            del self.opponent[opponent]

        if client in self.opponent:
            del self.opponent[client]
        
        if client in self.client_names:
            del self.client_names[client]

        if opponent in self.client_names:
            del self.client_names[opponent]
        
        if client in self.rooms:
            del self.rooms[client]
        
        if opponent in self.rooms:
            del self.rooms[opponent]
        
        client.close()

    def handle_receive(self, message, client):
        print(message)
        r_type = message.get("type")
        data = message.get("data")
        room = self.rooms[client]

        if r_type != Protocols.Request.ANSWER:
            return
        
        correct = room.verify_answer(client, data)
        if not correct:
            self.send(Protocols.Response.ANSWER_INVALID, None, client)
            return
        
        if room.indexs[client] >= len(room.questions):
            if not room.finished:
                self.db.increase_wins(self.client_names[client])
                self.db.increase_losses(self.client_names[self.opponent[client]])
                room.finished = True
            
            self.send_to_opponent(Protocols.Response.WINNER, self.client_names[client], client)
            self.send(Protocols.Response.WINNER, self.client_names[client], client)
        else:
            self.send_to_opponent(Protocols.Response.OPPONENT_ADVANCE, None, client)
            self.send(Protocols.Response.ANSWER_VALID, None, client)

    def send(self, r_type, data, client):
        message = {"type": r_type, "data": data}
        message = json.dumps(message).encode("ascii")
        client.send(message)

    def send_to_opponent(self, r_type, data, client):
        opponent = self.opponent.get(client)
        if not opponent:
            return
        self.send(r_type, data, opponent)

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()


if __name__ == "__main__":
    server = Server()
    server.receive()