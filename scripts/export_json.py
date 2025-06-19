import sqlite3
import json

def export_pokemon_data():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, type1, type2, hp, attack, defense, special_attack, special_defense, speed FROM pokemon")
    rows = cursor.fetchall()

    data = {}
    for name, type1, type2, hp, atk, def_, spa, spd, spe in rows:
        types = [type1]
        if type2 and type2.lower() != "none":
            types.append(type2)

        data[name] = {
            "types": types,
            "base_stats": {
                "hp": hp,
                "attack": atk,
                "defense": def_,
                "special_attack": spa,
                "special_defense": spd,
                "speed": spe
            },
            "learnset": {
                "level_up": [],
                "tm": [],
                "hm": []
            }
        }

    # Fetch moves and learning methods
    cursor.execute("SELECT pokemon_name, move_name, method, level_learned FROM pokemon_moves")
    move_rows = cursor.fetchall()

    for pokemon, move, method in move_rows:
        if pokemon in data:
            method = method.lower()
            if method == "level" and move not in data[pokemon]["learnset"]["level_up"]:
                data[pokemon]["learnset"]["level_up"].append(move)
            elif method == "tm" and move not in data[pokemon]["learnset"]["tm"]:
                data[pokemon]["learnset"]["tm"].append(move)
            elif method == "hm" and move not in data[pokemon]["learnset"]["hm"]:
                data[pokemon]["learnset"]["hm"].append(move)

    with open("static/data/pokemon.json", "w") as f:
        json.dump(data, f, indent=2)

    conn.close()

def export_move_data():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM moves")
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()

    data = {row[0]: dict(zip(columns, row)) for row in rows}

    with open("static/data/moves.json", "w") as f:
        json.dump(data, f, indent=2)

    conn.close()

if __name__ == "__main__":
    export_pokemon_data()
    export_move_data()
    print("Successfully generated pokemon.json and moves.json.")
