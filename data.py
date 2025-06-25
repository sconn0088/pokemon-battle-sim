import json
from models import Move

with open("static/data/moves.json", "r") as f:
    move_data = json.load(f)

ALL_MOVES = [Move(**data) for data in move_data.values()]