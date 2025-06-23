import sqlite3, os
import pandas as pd
from dataclasses import dataclass
from typing import Optional

BASE_DIR = os.path.dirname(__file__)
CSV_DIR = os.path.join(BASE_DIR, "data", "gen_1")

POKEMON_CSV = os.path.join(CSV_DIR, "pokemon_gen_1.csv")
MOVES_CSV = os.path.join(CSV_DIR, "moves_gen_1.csv")
POKEMON_MOVES_CSV = os.path.join(CSV_DIR, "pokemon_moves_gen_1.csv")

@dataclass
class Move:
    name: str
    type: str
    power: int
    accuracy: int
    category: str
    description: str
    target: str
    effect: Optional[str] = None
    status: Optional[str] = None
    chance: Optional[int] = 100
    stat: Optional[str] = None
    stages: Optional[int] = 0
    hits: Optional[str] = None
    duration: Optional[str] = None
    critical_rate: Optional[float] = 1/24
    multi_turn: Optional[str] = None
    multi_turn_type: Optional[str] = None
    vulnerable_to: Optional[str] = None
    effect_value: Optional[float] = 0.0

    def __str__(self):
        return f"{self.name} ({self.type})"

@dataclass
class Pokemon:
    def __init__(self, name, level, types, base_stats, moves):
        self.name = name
        self.level = level
        self.types = types

        self.hp = calculate_stat(base_stats["hp"], level)
        self.attack = calculate_stat(base_stats["attack"], level)
        self.defense = calculate_stat(base_stats["defense"], level)
        self.special_attack = calculate_stat(base_stats["special_attack"], level)
        self.special_defense = calculate_stat(base_stats["special_defense"], level)
        self.speed = calculate_stat(base_stats["speed"], level)

        self.stat_stages = {
          "attack": 0,
          "defense": 0,
          "special_attack": 0,
          "special_defense": 0,
          "speed": 0,
          "accuracy": 0,
          "evasiveness": 0
        }

        self.current_hp = self.hp
        self.moves = moves
        self.current_move = None

        self.transformed = False

        self.status = "OK"

        self.disabled_move = None
        self.disabled_turns = 0

        self.is_confused = False
        self.confused_turns = 0

        self.sleep_turns = 0

        self.toxic_counter = 0

        self.flinched = False

        self.next_crit_boosted = False

        self.multi_turn_move = None
        self.multi_turn_counter = 0
        
        self.must_charge = False
        self.must_recharge = False

        self.invulnerable = False
        self.vulnerable_to = []

        self.is_biding = False
        self.bide_damage = 0

    def is_fainted(self):
        return self.current_hp <= 0

@dataclass
class BattleLog:
    def __init__(self):
        self.entries = []

    def add(self, message):
        self.entries.append(message)

    def export_to_file(self, filename="battle_log.txt"):
        with open(filename, "w") as f:
            f.write("\n".join(self.entries))

    def get_log_text(self):
        return "\n".join(self.entries)

def create_database():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon (
        name TEXT PRIMARY KEY,
        type1 TEXT,
        type2 TEXT,
        hp INTEGER,
        attack INTEGER,
        defense INTEGER,
        special_attack INTEGER,
        special_defense INTEGER,
        speed INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moves (
        name TEXT PRIMARY KEY,
        type TEXT,
        power INTEGER,
        accuracy INTEGER,
        category TEXT,
        description TEXT,
        effect TEXT,
        status TEXT,
        chance INTEGER,
        target TEXT,
        stat TEXT,
        stages INTEGER,
        hits TEXT,
        duration TEXT,
        critical_hit REAL,
        multi_turn TEXT,
        multi_turn_type TEXT,
        vulnerable_to TEXT,
        effect_value REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_moves (
        pokemon_name TEXT,
        move_name TEXT,
        method TEXT,
        level_learned INTEGER,
        FOREIGN KEY (pokemon_name) REFERENCES pokemon(name),
        FOREIGN KEY (move_name) REFERENCES moves(name)
    )
    """)

    conn.commit()
    conn.close()

def load_data_from_csv():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    # Load Pokémon
    df_pokemon = pd.read_csv(POKEMON_CSV)
    for _, row in df_pokemon.iterrows():
        cursor.execute("""
        INSERT OR IGNORE INTO pokemon VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(row))

    # Load Moves
    df_moves = pd.read_csv(MOVES_CSV)
    for _, row in df_moves.iterrows():
        cursor.execute("""
        INSERT OR IGNORE INTO moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(row))

    # Load Pokémon-Move relationships
    df_pmoves = pd.read_csv(POKEMON_MOVES_CSV)
    for _, row in df_pmoves.iterrows():
        cursor.execute("""
        INSERT OR IGNORE INTO pokemon_moves VALUES (?, ?, ?, ?)
        """, tuple(row))

    conn.commit()
    conn.close()

def load_pokemon(name: str) -> Pokemon:
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pokemon WHERE name = ?", (name,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Pokemon '{name}' not found.")

    cursor.execute("""
    SELECT m.name, m.type, m.power, m.accuracy, m.category
    FROM moves m
    JOIN pokemon_moves pm ON m.name = pm.move_name
    WHERE pm.pokemon_name = ?
    """, (name,))
    move_rows = cursor.fetchall()

    moves = [Move(*m) for m in move_rows]

    conn.close()

    return Pokemon(
        name=row[0],
        type1=row[1],
        type2=row[2],
        hp=row[3],
        attack=row[4],
        defense=row[5],
        special_attack=row[6],
        special_defense=row[7],
        speed=row[8],
        moves=moves
    )
def get_all_pokemon():
    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM pokemon ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]

def calculate_stat(base_stat, level):
    return int((((2 * base_stat + 94) * level) / 100) + level + 10)
