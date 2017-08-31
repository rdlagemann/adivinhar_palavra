import os
import socket
import sys
import threading
import time
import select 
from random import randint


class Player(object):
	ready_to_play = False
	points = 0
	current_guess = ''
	online = False


	def __init__(self, name, conn, addr, n_tries):
		self.name = name
		self.conn = conn
		self.addr = addr
		self.tries_left = n_tries
		self.online = True
		

	def has_tries(self):
		return self.tries_left > 0

	def is_alive(self):
		return self.tries_left > 0



class GameManager(object):
	#### Internal default configs #####      
	point_factor = 10
	n_tries = 4
	commands = ['$q', '$r']
	game_running = False


	default_messages = {
		"hit" : "-:*.* {0} scored {1} points ! *.*:-\n",
		"miss": "_ {0} lost {1} try! _\n",
		"dead": "{0}, you have no more tries. Wait until next word.\n"
	}	

	player_stats_display = '''
	player: {0}		
	tries: {1}		
	points: {2}		
	+---------------+'''

	word_stat_display = '''
	======== WORD =========================
									  
		{0}							  
										  
	=======================================
	\n
	'''
 	


	####################################

	already_played_letters = []
	players = []
	round_messages = []
	valid_letters_played = []

	word_to_guess = ""
	def __init__(self, words_filename):
		# self.word_to_guess = "ala"
		self.display = ' _' * len(self.word_to_guess)
		with open(words_filename, 'r') as f:
			self.words_to_play = f.readlines()
		self.words_to_play = [w.strip() for w in self.words_to_play]



	def define_screen(self):
		players_d = ''
		word_d = ''
		screen = ''
		played = '''
		played:
		'''

		for l in self.already_played_letters:
		
			played += l + ', '

		for p in self.players:
			players_d += self.player_stats_display.format(p.name, p.tries_left, p.points)
	
		word_d = self.word_stat_display.format(self.display)
		screen = players_d + word_d + played + '\n'

		return screen



	def generate_new_word(self, old_word):
		chosen_one = old_word
		while chosen_one == old_word:
			chosen_one = self.words_to_play[randint(0, len(self.words_to_play) - 1)]
		return chosen_one


	def update_game_status(self):
		self.display = ""
		charac = ""
		for l in self.word_to_guess:
			if l in self.already_played_letters:
				charac = l
			else:
				charac = " _ "

			self.display += charac


	def get_all_guesses(self):
		return [(p.current_guess, p.addr) for p in self.players]

	def is_command(self, input):
		return input[0] == "$"

	def handle_command(self, command):
		print("it's maybe a command!")
		pass

	# handle guesses that are equal
	def refactor_guesses(self):
		all_guesses = self.get_all_guesses()
		refac = {}
		for (guess, addr) in all_guesses:
			if not self.is_command(guess):			
				if guess not in refac:
					refac[guess] = []

			if (addr not in refac[guess]) and (not self.is_command(guess)):
				refac[guess].append(addr)

			else:
				self.handle_command((guess, addr))		
		
		return refac

	def players_alive(self):
		counter = 0
		for p in self.players:
			if p.is_alive():
				counter += 1
		return counter

	def is_game_running(self):
		dead = 0
		for p in self.players:
			if not p.is_alive():
				dead += 1
		#tem que ter mais vivos que mortos e ter alguem de fato		
		return (self.players_alive() > 0) and (len(self.players) > 0)

	def is_round_running(self):
		return ('_' in self.display) and self.players_alive()

	def update_already_played(self, letter):
		if letter not in self.already_played_letters:
			self.already_played_letters.append(letter)
		else:
			print("letter ->", letter, " already in already_pla")

	def check_hit(self, guess):
		if len(guess) > 1:
			if guess == self.word_to_guess:
				return True
			else:
				return False

		return guess in self.word_to_guess and (not guess in self.already_played_letters)


	def calculate_points(self, guess, n_guesses):
		if n_guesses == 0:
			n_guesses = 1

		#acertou a palavra toda
		if len(guess) > 1:
			return 50.0/n_guesses

		#acertou uma letra
		return (self.point_factor *  self.word_to_guess.count(guess))/n_guesses

	def update_points(self, addr_list, points):
		for p in self.players:
			if p.addr in addr_list:
				p.points += points


	def update_round_messages(self, addr_list, type, value):
		for p in self.players:
			if p.addr in addr_list:
				self.round_messages.append(self.default_messages[type].format(p.name, value))

	
	def decrement_tries_left(self, addr_list, value):
		for p in self.players:
			if p.addr in addr_list:
				p.tries_left -= value

	def reset_tries(self):
		for p in self.players:
			p.tries_left = self.n_tries

	
	def config_new_game(self):
		self.already_played_letters[:] = []
		self.word_to_guess = self.generate_new_word(self.word_to_guess)
		self.update_game_status()
		self.reset_tries()
		
	
	def play_round(self):
		guess_addrs_dict = self.refactor_guesses()
		if not len(guess_addrs_dict):
			return False

		n_guesses = 0
		self.round_messages[:] = []

		points = 0

		for guess in guess_addrs_dict:
			
			
			addr_list = guess_addrs_dict[guess][:]
			#valid_letters_played = []
			#acertou
			if self.check_hit(guess): 
				n_guesses = len(addr_list)
				points = self.calculate_points(guess, n_guesses)

				self.update_points(addr_list, points)
				self.update_round_messages(addr_list, "hit", points)

				for l in guess:
					print("\n um letra: ", l)
					self.valid_letters_played.append(l)
	
				
			# errou
			else: 
				tries_lost = len(guess)
				self.decrement_tries_left(addr_list, tries_lost)
				self.update_round_messages(addr_list, "miss", tries_lost)

				if len(guess) == 1:
					print("Guess is: " + guess + " valid and INcorrect!")
					self.valid_letters_played.append(guess)

		for guess in self.valid_letters_played:
			print("updating : ", guess, " : to already played")
			self.update_already_played(guess)

		self.update_game_status()

		self.valid_letters_played[:] = []
		
		return True
#
# global vars which will be shared by the threads
# 
GM = GameManager("words_to_play.txt")

GAME_READY = False
max_plyrs = 4
min_plyrs = 1


#
# function definitions
#

def join_all_threads(list_trds):
	for t in list_trds:
		t.join()


def player_signal(player, signal):				
	player.conn.sendto(str.encode(signal), player.addr)	


def conditions_ready():
	for c in GM.players:
		if not c.ready_to_play:
			return False

	return len(GM.players) >= min_plyrs

def room_is_full():
	return len(GM.players) == max_plyrs


# TODO: talvez usar essa função pra testa se um player ainda esta online, se não estiver remove da lista GM.players
def msg_to_all(msg):
	global GM

	for player in GM.players:
		# print("delivering to...", player.name)
		try:
			player.conn.sendto(str.encode(msg), player.addr)
			# print("...OK.")	
		except:
			print("< " + player.name + " LEFT THE LOBBY >\n")
			GM.players.remove(player)
			break

def online_in_lobby():
	global GM
	string = "\n Players Online: \n "

	for player in GM.players:
		string = string + player.name + "\n"

	return string +  "\n\n<Type [$r]eady to play >\n"



def chat_thread(player):
	global GM
	print("chat thread start")

	while not conditions_ready():

	
		data = player.conn.recv(2048).decode('utf-8')

		if data == '' or data == '$q':
			msg_to_all("< " + player.name + " LEFT THE LOBBY >")
			GM.players.remove(player)

		elif data == '$h':
			print("\n entrou help")
			reply = '< ' + player.name + ' is reading help message. >'

		elif data == '$r':	# player signal ready
			msg_to_all('<'+ player.name + ' is ready.>')
			player.ready_to_play = True
			if GM.game_running:
			 	reply = ":busy"
			 	p.conn.sendto(str.encode(reply), player.addr)
			break
		else:
			reply = '[' + player.name + ']' + data + "\n"

		# finally send a reply for all GM.players
		for p in GM.players:
			if p.addr != player.addr:			
				print("delivering to...", p.name)
				p.conn.sendto(str.encode(reply), player.addr)



# verify if all players make their guess so then can proceed
time_to_guess = 200
def player_guess_thread(player):
	global GM
	data = ''

	player.conn.sendto(str.encode(("> make a guess ({0} seconds):".format(time_to_guess))), player.addr)

	ready = select.select([player.conn], [], [], time_to_guess)
	
	if ready[0]:
		data = player.conn.recv(2048).decode()

	else:
		player.conn.sendto(str.encode("Lost your turn! :("), player.addr)
		data = ''

	player.current_guess = data
	print(player.name, ": guess = ", player.current_guess)



def server_game_thread():
	global GM
	GM.game_running = True

	# for the game
	while GM.is_game_running(): 
		msg_to_all("<NEW GAME STARTED.> \n")
		GM.config_new_game()

		while GM.is_round_running():
			guess_trds = []

			msg_to_all("The word to be guessed is: \n")
			msg_to_all(GM.define_screen())

			# guess thread creation for all players
			for player in GM.players:
				# for each guess
				if player.has_tries():
					t = threading.Thread(target = player_guess_thread, args = (player,))
					t.start()
					guess_trds.append(t)
				
				else:
					# player have no more tries, cant guess anymore
					player.conn.sendto(str.encode(GM.default_messages["dead"].format(player.name)), player.addr)

			
			for tr in guess_trds:
				tr.join()

			# after all players thread returned a guess 
			GM.play_round()


			for m in GM.round_messages:
				msg_to_all(m)

			if not '_' in GM.display:
				msg_to_all("Alright! The word was " + GM.word_to_guess.upper() + " !" )
				time.sleep(3)




	GM.game_running = False
	msg_to_all("< GAME OVER >")
	time.sleep(3)



def lobby_open_thread():
	# talvez criar locks pra essas variaveis?
	global GAME_READY
	global GM
	# players_thread = []

	print("<Players (" + str(len(GM.players)) + "/" + str(max_plyrs) + ")>") 
	while not room_is_full() and (not conditions_ready()): #TODO: dando pau pra 3 players, nao finaliza as threads direito
		# TODO: verificar quando um player desconecta e remover da lista GM.players[]
		print(".", end='', flush=True)
		try:
			conn, addr = s.accept()

			name = conn.recv(2048).decode('utf-8')
			player = Player(name, conn, addr, GM.n_tries)
			GM.players.append(player)

			print("<Players (" + str(len(GM.players)) + "/" + str(max_plyrs) + ")>")
			msg_to_all( "<" + player.name + " JOINED THE LOBBY >" )
			player.conn.sendto(str.encode(online_in_lobby()), player.addr)

			# runs chat from lobby
			t = threading.Thread(target = chat_thread, args = (player, )).start()
			# players_thread.append(t)



		
		except:
			# non blocking socket
			time.sleep(0.5)
			pass		

	msg_to_all("< GAME WILL START >\n")

#
# initial config
#

#thanks to: https://stackoverflow.com/a/33245570
f = os.popen('ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1')
host = f.read()

#host = '192.168.25.7'
port = 6000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setblocking(0)

# bind
try:
	s.bind((host, port))
except socket.error as e:
	print(str(e))
s.listen(5)

#
# run lobby
#
lobby_t = threading.Thread(target = lobby_open_thread)
lobby_t.start()

lobby_t.join()



time.sleep(1)


game_t = threading.Thread(target = server_game_thread)


game_t.start()
game_t.join()

msg_to_all(":gameover")

s.close()


