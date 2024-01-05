import os, sys
from dataclasses import dataclass
import dataclasses
from typing import List
import copy
import itertools
import subprocess
from enum import Enum
import json

dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir)

from py_bots import bots as raw_bots

# The set of bots
bots = []

class BrainType(Enum):
	JAVASCRIPT = 1
	PYTHON = 2
	UNKNOWN = 3

@dataclass
class SetData:
	# The current round
	current_round: int

	# Your current score
	self_score: int

	# Your opponents current score
	other_score: int

	# A historic list of your choices (len=current_round)
	self_choices: List[bool]

	# A historic list of your opponents choices (len=current_round)
	other_choices: List[bool]

@dataclass
class GameData:
	# The number of rounds that will be played. Default=100
	total_rounds: int

	# The points you gain by cooperating with your partner. Default=5
	cooperation_win: int

	# The points you gain by attempting to cooperate, while your partner defects. Default=1
	cooperation_loss: int

	# The points you win by defecting, when your partner cooperates. Default=5
	defect_win: int

	# The points you gain by defecting, when your partner also defects. Default=0
	defect_loss: int 

	# The points you gain by winning an entire set (promotes aggression): Default=0
	win_bonus_points: int

	# The points you gain by tying with your partner, after an entire set is complete.
	# Is not paid out if you defected every round (promotes cooperation): Default=0
	cooperation_bonus: int

	# The points you *lose* by defecting every round, against an equally miserly opponent (promotes cooperation?): Default=0
	defect_penalty: int

class Bot:
	def __init__(self, py_brain=None, js_brain=None, bot_type=BrainType.UNKNOWN, total_score=0, name=None) -> None:
		self.py_brain = py_brain
		self.js_brain = js_brain
		self.bot_type = bot_type
		self.total_score = total_score

		# Match related
		self.current_round = 0
		self.score = 0
		self.choices = []
		self.name = name
		self.game_data = None

	@classmethod
	def py_bot(cls, py_brain):
		return cls(py_brain=py_brain, name=py_brain.get_name(), bot_type=BrainType.PYTHON)

	@classmethod
	def js_bot(cls, js_brain):
		name = subprocess.check_output(['npx','run-func', js_brain,'getName'], shell=True).decode().strip()
		return cls(js_brain=js_brain, name=name, bot_type=BrainType.JAVASCRIPT)

	# Called when a match begins
	def start_match(self, game_data: GameData):
		self.score = 0
		self.choices = []
		self.game_data = game_data
		self.current_round = 0

		self.start(game_data)


	def execute_js_function(self, func_name, arg, wants_ret):
		results = subprocess.check_output(['npx','run-func', self.js_brain, func_name, arg], shell=True).decode()


		split = results.split("\n")

		if wants_ret:
			if len(split) > 1:
				split.pop()

		logs = split[:-1]
		ret = split[-1]

		for log in logs:
			print(f"	-- '{self.name}': {log}")

		return ret



	def play(self, data):
		if self.bot_type == BrainType.PYTHON:
			return self.py_brain.play(data)
		else:
			ret = self.execute_js_function('play', json.dumps(dataclasses.asdict(data)), True)
			print(f"Testing {ret=}")
			if ret == "true":
				return True
			else:
				return False
	
	def start(self, data):
		if self.bot_type == BrainType.PYTHON:
			self.py_brain.start(data)
		else:
			self.execute_js_function('start', json.dumps(dataclasses.asdict(data)), False)
	
	def apply_results(self, self_choice, other_choice):
		self.current_round += 1		
		self.choices.append(self_choice)

		# Cooperation
		if self_choice:
			# Cooperation win
			if other_choice:
				self.score += self.game_data.cooperation_win
			else:
				self.score += self.game_data.cooperation_loss
		# Defect
		else:
			# Defect win
			if other_choice:
				self.score += self.game_data.defect_win
			else:
				self.score += self.game_data.defect_loss

	def get_set_data(self, other):
		return SetData(self.current_round, self.score, other.score, self.choices, other.choices)
		
	def finish_match(self, other):
		bonus_points = 0 

		# Assign round-win points
		if self.score > other.score:
			bonus_points += self.game_data.win_bonus_points

		# TODO: Assign cooperation points
		
		self.total_score += self.score
		self.total_score += bonus_points
"""
Runs an entire tournament
"""
def run_tournament(data: GameData):
	print(f"Starting Tournament: {data.total_rounds=}")

	bots = []

	# Load Python Bots
	for bot in raw_bots:
		bots.append(Bot.py_bot(py_brain=bot))

	for file_name in os.listdir("./js_bots"):
		bots.append(Bot.js_bot(js_brain="js_bots/" + file_name))

	for a, b in itertools.combinations_with_replacement(bots, 2):

		# When facing oneself, we need to ensure that the copy doesn't contribute
		# score to the original bot
		if a == b:
			b = copy.copy(b)

		run_set(data, a, b)

	print("\n\nRESULTS:")
	for bot in sorted(bots, key=lambda x: x.total_score, reverse=True):
		print(f"	{bot.name}={bot.total_score}")


def run_set(game_data: GameData, bot_a : Bot, bot_b: Bot):
	print("\n--")
	print(f"Running Set: {bot_a.name} Vs. {bot_b.name}")

	bot_a.start_match(game_data)
	bot_b.start_match(game_data)

	for i in range(game_data.total_rounds):
		choice_a = bot_a.play(bot_a.get_set_data(bot_b))
		choice_b = bot_b.play(bot_b.get_set_data(bot_a))

		print(f"	Running Round: {bot_a.name}={choice_a}, {bot_b.name}={choice_b}")

		bot_a.apply_results(choice_a, choice_b)
		bot_b.apply_results(choice_b, choice_a)

	print(f"Set finished: {bot_a.name}={bot_a.score}, {bot_b.name}={bot_b.score}")

	bot_a.finish_match(bot_b)
	bot_b.finish_match(bot_a)


def main():
	game_data = GameData(10, 3, 0, 5, 1, 0, 0, 0)
	run_tournament(game_data)

if __name__ == '__main__':
	main()