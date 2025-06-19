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

    learnsets = {}
    for name, move, method, level in move_rows:
        if name not in learnsets:
            learnsets[name] = {"level_up": [], "tm": [], "hm": []}
        if method == "level":
            learnsets[name]["level_up"].append({"name": move, "level": level})
        elif method == "TM":
            learnsets[name]["tm"].append(move)
        elif method == "HM":
            learnsets[name]["hm"].append(move)

    # Merge learnset into the existing data dictionary
    for name in data:
        if name in learnsets:
            data[name]["learnset"] = learnsets[name]

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
