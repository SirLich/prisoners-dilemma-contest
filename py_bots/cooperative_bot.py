import random
from manager import SetData, GameData

def play(set_data : SetData):
	# Cooperate as long as we're winning, or tied
	return set_data.self_score >= set_data.other_score


def start(game_data: GameData):
	pass

def get_name() -> str:
	return "Cooperative Bot"