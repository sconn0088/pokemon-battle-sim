from flask import Flask, jsonify, request, abort, send_from_directory
import models as m
from pokemon_battle_simulator import simulate_battle
from utils import create_pokemon_from_data
import sqlite3

app = Flask(__name__)

with app.app_context():
    m.create_database()
    m.load_data_from_csv()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/pokemon/<name>", methods=["GET"])
def get_pokemon(name):
    try:
        p = m.load_pokemon(name)
        return jsonify({
            "name": p.name,
            "type1": p.type1,
            "type2": p.type2,
            "hp": p.hp,
            "attack": p.attack,
            "defense": p.defense,
            "special_attack": p.special_attack,
            "special_defense": p.special_defense,
            "speed": p.speed,
            "moves": [move.__dict__ for move in p.moves]
        })
    except ValueError as e:
        abort(404, description=str(e))

@app.route("/moves", methods=["GET"])
def list_moves():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, type, power, accuracy, category, description FROM moves")
    moves = cursor.fetchall()
    conn.close()
    return jsonify([{
        "name": m[0], "type": m[1], "power": m[2], "accuracy": m[3], "category": m[4], "description": m[5]
    } for m in moves])

@app.route("/pokemon", methods=["POST"])
def add_pokemon():
    data = request.get_json()
    try:
        conn = sqlite3.connect("pokedex.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pokemon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"], data["type1"], data.get("type2", ""), data["hp"],
            data["attack"], data["defense"],
            data["special_attack"], data["special_defense"], data["speed"]
        ))
        for move in data["moves"]:
            cursor.execute("INSERT OR IGNORE INTO moves VALUES (?, ?, ?, ?, ?)", (
                move["name"], move["type"], move["power"], move["accuracy"], move["category"]
            ))
            cursor.execute("INSERT INTO pokemon_moves VALUES (?, ?)", (data["name"], move["name"]))
        conn.commit()
        conn.close()
        return jsonify({"message": "Pokemon added."}), 201
    except Exception as e:
        abort(400, description=str(e))

@app.route("/move", methods=["POST"])
def add_move():
    data = request.get_json()
    try:
        conn = sqlite3.connect("pokedex.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO moves VALUES (?, ?, ?, ?, ?)", (
            data["name"], data["type"], data["power"], data["accuracy"], data["category"]
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Move added."}), 201
    except Exception as e:
        abort(400, description=str(e))

@app.route("/api/pokemon-list")
def pokemon_list():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM pokemon ORDER BY name ASC")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(names)

@app.route("/api/moves")
def get_moves():
    name = request.args.get("name")
    level = int(request.args.get("level", 100))
    allow_tm = request.args.get("tm", "false").lower() == "true"

    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    if allow_tm:
        cursor.execute("""
            SELECT m.name, m.type, m.power, m.accuracy, m.category, m.description
            FROM moves m
            JOIN pokemon_moves pm ON m.name = pm.move_name
            WHERE pm.pokemon_name = ?
              AND (
                    (pm.method = 'level' AND pm.level_learned <= ?)
                 OR (pm.method IN ('TM', 'HM'))
              )
        """, (name, level))
    else:
        cursor.execute("""
            SELECT m.name, m.type, m.power, m.accuracy, m.category, m.description
            FROM moves m
            JOIN pokemon_moves pm ON m.name = pm.move_name
            WHERE pm.pokemon_name = ?
              AND pm.method = 'level'
              AND pm.level_learned <= ?
        """, (name, level))

    moves = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "name": m[0],
            "type": m[1],
            "power": m[2],
            "accuracy": m[3],
            "category": m[4],
            "description": m[5]
        }
        for m in moves
    ])

@app.route("/api/pokemon", methods=["GET"])
def get_all_pokemon_route():
    try:
        data = m.get_all_pokemon()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def simulate_many_battles(player_data, opponent_data, num_trials=1000):
    from utils import create_pokemon_from_data
    import models as m

    player_wins = 0
    opponent_wins = 0
    sample_log = ""

    for i in range(num_trials):
        player = create_pokemon_from_data(player_data)
        opponent = create_pokemon_from_data(opponent_data)
        log = m.BattleLog()
        result = simulate_battle(player, opponent, log)
        if i == 0:
            sample_log = log.get_log_text()
        if result == player.name:
            player_wins += 1
        elif result == opponent.name:
            opponent_wins += 1

    return {
        "player_percent": round((player_wins / num_trials) * 100, 1),
        "opponent_percent": round((opponent_wins / num_trials) * 100, 1),
        "log": sample_log
    }

@app.route("/api/battle", methods=["POST"])
def battle():
    data = request.get_json()

    player_data = data.get("player")
    opponent_data = data.get("opponent")

    if not player_data or not opponent_data:
        return jsonify({"error": "Invalid request data"}), 400

    try:
        result_data = simulate_many_battles(player_data, opponent_data, num_trials=1000)

        return jsonify({
            "result": f"{player_data['name']} wins {result_data['player_percent']}% of the time!",
            "battle_log": result_data["log"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
