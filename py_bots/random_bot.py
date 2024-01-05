import random
from manager import SetData, GameData

def play(set_data : SetData):
	return random.choice([True, False])

def start(game_data: GameData):
	pass

def get_name() -> str:
	return "Random Bot"