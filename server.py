import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      AlreadyHerePlayerList = {"cmd": 3, "players": []}
      if addr in clients:
         if 'heartbeat' in data:
            # If the server receives a heartbeat message, it updates the corresponding client with the last heartbeat time. 
            clients[addr]['lastBeat'] = datetime.now()
      else:
         if 'connect' in data: # the server expects a packet with "connect" in order for a client to connect
            # When a new client connects, the server adds the new client to a list of clients it has.
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            message = {"cmd": 0,"player":{"id":str(addr)}}
            m = json.dumps(message)
            
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1])) # When a new client connects, 
               # the server sends a message to all currently connected clients
               player = {}
               player['id'] = str(c)
               AlreadyHerePlayerList['players'].append(player)

            # since we are already iterating through clients, store id of each
            ncm = json.dumps(AlreadyHerePlayerList)
            # send id of each client TO NEW CLIENT after storing it
            sock.sendto(bytes(ncm,'utf8'), (addr[0],addr[1]))




               

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
            # If a client is dropped, the server sends a message to all clients currently connected 
            # to inform them of the dropped player. 
            for cc in clients: # the client has been dropped, now iterate through all connected clients
               droppedClientMsg = {"cmd": 2, "id":str(c)} # get the id of the client that dropped 
               dcp = json.dumps(droppedClientMsg) # store in json
               sock.sendto(bytes(dcp,'utf8'), (cc[0],cc[1])) # send json to each client
               print('Sent message to current client informing of dropped client')
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
