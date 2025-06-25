from models import Pokemon, Move
import random

def create_pokemon_from_data(data):
    name = data["name"]
    level = data["level"]
    types = data["types"]

    base_stats = data["base_stats"]
    moves = []

    for move_data in data["moves"]:
        move = Move(
            name=move_data["name"],
            type=move_data["type"],
            category=move_data["category"],
            power=move_data.get("power", 0),
            accuracy=move_data.get("accuracy", 100),
            description=move_data.get("description", ""),
            target=move_data.get("target", "opponent")
        )
        move.effect = move_data.get("effect")
        move.chance = int(move_data["chance"]) if move_data.get("chance") is not None else 100
        move.stat = move_data.get("stat")
        move.stages = int(move_data["stages"]) if move_data.get("stages") is not None else 0
        move.status = move_data.get("status")
        move.duration = move_data.get("duration", "")
        move.effect_value = float(move_data["effect_value"]) if move_data.get("effect_value") is not None else 0.0
        move.hits = move_data.get("hits")
        move.critical_rate = float(move_data["critical_rate"]) if move_data.get("critical_rate") is not None else 0.0
        move.multi_turn = move_data.get("multi_turn")
        move.multi_turn_type = move_data.get("multi_turn_type")
        move.vulnerable_to = move_data.get("vulnerable_to")
        moves.append(move)

    return Pokemon(name, level, types, base_stats, moves)

def select_move(pokemon):
    if pokemon.multi_turn_move is not None:
        pokemon.current_move = pokemon.multi_turn_move
        return
    move = random.choice(pokemon.moves)
    pokemon.current_move = move

# Moves Metronome should NOT pick
METRONOME_BLACKLIST = [
    "Metronome", "Mirror Move"
]