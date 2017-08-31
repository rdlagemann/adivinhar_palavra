import socket
import sys
import threading

help_message = '''
***** help ******
General:
Enter '$r' to be ready to play.
	When everybody is [$r]eady, the game will start.
Enter '$q' to quit the game.

Game:
	You should guess the secret word letter by letter.
	Loses one(1) try if you guess a lettr wrong.
	You also can guess the whole word, but be carefull, if you guess it wrong you can lose many tries.
	Four(4) tries for each word is all you have.
	Good Luck!
'''

def send_msg():
	while True:
		msg = input("")
		if msg == '$q':
			s.sendall(str.encode(msg))
			break
		elif msg == '$h':
			print(help_message)

		s.sendall(str.encode(msg))

def recv_msg():
	while True:
		server_reply = s.recv(4096).decode('utf-8')

		if server_reply == ":gameover":
			print("GAME OVER: Thanks for Playing!")
			break
		elif server_reply == ":busy":
			print("Game is running. Can't connect now.")
			break
		else:
			print(server_reply + '\n')



# socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = ''
port = 6000

#configure player name and  server IP
nickname = ''
while True:
	nickname = input("Enter your nickname: ")
	if (len(nickname) < 2) or (len(nickname) > 10):
		nickname = input("Enter your nickname (2 to 10 characters lenght):")
	else:
		break


host = input("Connect to IP: ")

s.connect((host, port))
s.sendall(str.encode(nickname))


print('|--------------- Lobby: chat -------------------|')
print("loading...")


send_t = threading.Thread(target = send_msg)
recv_t = threading.Thread(target = recv_msg)


send_t.start()
recv_t.start()

send_t.join()
recv_t.join()


print('connection finished')

s.close()
