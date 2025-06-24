TYPE_EFFECTIVENESS = {
    ('Normal', 'Rock'): 0.5, ('Normal', 'Ghost'): 0.0, ('Normal', 'Steel'): 0.5,
    ('Fighting', 'Normal'): 2.0, ('Fighting', 'Rock'): 2.0, ('Fighting', 'Steel'): 2.0,
    ('Fighting', 'Ice'): 2.0, ('Fighting', 'Dark'): 2.0, ('Fighting', 'Ghost'): 0.0,
    ('Fighting', 'Flying'): 0.5, ('Fighting', 'Poison'): 0.5, ('Fighting', 'Bug'): 0.5,
    ('Fighting', 'Psychic'): 0.5, ('Fighting', 'Fairy'): 0.5,
    ('Flying', 'Fighting'): 2.0, ('Flying', 'Bug'): 2.0, ('Flying', 'Grass'): 2.0,
    ('Flying', 'Rock'): 0.5, ('Flying', 'Steel'): 0.5, ('Flying', 'Electric'): 0.5,
    ('Poison', 'Grass'): 2.0, ('Poison', 'Fairy'): 2.0,
    ('Poison', 'Poison'): 0.5, ('Poison', 'Ground'): 0.5, ('Poison', 'Rock'): 0.5, ('Poison', 'Ghost'): 0.5,
    ('Poison', 'Steel'): 0.0,
    ('Ground', 'Poison'): 2.0, ('Ground', 'Rock'): 2.0, ('Ground', 'Steel'): 2.0, ('Ground', 'Fire'): 2.0, ('Ground', 'Electric'): 2.0,
    ('Ground', 'Bug'): 0.5, ('Ground', 'Grass'): 0.5, ('Ground', 'Flying'): 0.0,
    ('Rock', 'Flying'): 2.0, ('Rock', 'Bug'): 2.0, ('Rock', 'Fire'): 2.0, ('Rock', 'Ice'): 2.0,
    ('Rock', 'Fighting'): 0.5, ('Rock', 'Ground'): 0.5, ('Rock', 'Steel'): 0.5,
    ('Bug', 'Grass'): 2.0, ('Bug', 'Psychic'): 2.0, ('Bug', 'Dark'): 2.0,
    ('Bug', 'Fighting'): 0.5, ('Bug', 'Flying'): 0.5, ('Bug', 'Ghost'): 0.5, ('Bug', 'Steel'): 0.5, ('Bug', 'Fire'): 0.5, ('Bug', 'Fairy'): 0.5,
    ('Ghost', 'Ghost'): 2.0, ('Ghost', 'Psychic'): 2.0,
    ('Ghost', 'Normal'): 0.0, ('Ghost', 'Dark'): 0.5,
    ('Steel', 'Rock'): 2.0, ('Steel', 'Ice'): 2.0, ('Steel', 'Fairy'): 2.0,
    ('Steel', 'Steel'): 0.5, ('Steel', 'Fire'): 0.5, ('Steel', 'Water'): 0.5, ('Steel', 'Electric'): 0.5,
    ('Fire', 'Bug'): 2.0, ('Fire', 'Steel'): 2.0, ('Fire', 'Grass'): 2.0, ('Fire', 'Ice'): 2.0,
    ('Fire', 'Rock'): 0.5, ('Fire', 'Fire'): 0.5, ('Fire', 'Water'): 0.5, ('Fire', 'Dragon'): 0.5,
    ('Water', 'Ground'): 2.0, ('Water', 'Rock'): 2.0, ('Water', 'Fire'): 2.0,
    ('Water', 'Water'): 0.5, ('Water', 'Grass'): 0.5, ('Water', 'Dragon'): 0.5,
    ('Grass', 'Ground'): 2.0, ('Grass', 'Rock'): 2.0, ('Grass', 'Water'): 2.0,
    ('Grass', 'Flying'): 0.5, ('Grass', 'Poison'): 0.5, ('Grass', 'Bug'): 0.5, ('Grass', 'Steel'): 0.5, ('Grass', 'Fire'): 0.5, ('Grass', 'Grass'): 0.5, ('Grass', 'Dragon'): 0.5,
    ('Electric', 'Flying'): 2.0, ('Electric', 'Water'): 2.0,
    ('Electric', 'Grass'): 0.5, ('Electric', 'Electric'): 0.5, ('Electric', 'Dragon'): 0.5, ('Electric', 'Ground'): 0.0,
    ('Psychic', 'Fighting'): 2.0, ('Psychic', 'Poison'): 2.0,
    ('Psychic', 'Psychic'): 0.5, ('Psychic', 'Steel'): 0.5, ('Psychic', 'Dark'): 0.0,
    ('Ice', 'Flying'): 2.0, ('Ice', 'Ground'): 2.0, ('Ice', 'Grass'): 2.0, ('Ice', 'Dragon'): 2.0,
    ('Ice', 'Steel'): 0.5, ('Ice', 'Fire'): 0.5, ('Ice', 'Water'): 0.5, ('Ice', 'Ice'): 0.5,
    ('Dragon', 'Dragon'): 2.0, ('Dragon', 'Steel'): 0.5, ('Dragon', 'Fairy'): 0.0,
    ('Dark', 'Ghost'): 2.0, ('Dark', 'Psychic'): 2.0,
    ('Dark', 'Fighting'): 0.5, ('Dark', 'Dark'): 0.5, ('Dark', 'Fairy'): 0.5,
    ('Fairy', 'Fighting'): 2.0, ('Fairy', 'Dragon'): 2.0, ('Fairy', 'Dark'): 2.0,
    ('Fairy', 'Poison'): 0.5, ('Fairy', 'Steel'): 0.5, ('Fairy', 'Fire'): 0.5,
}

def get_type_multiplier(move_type, target_types):
    multiplier = 1.0
    for t in target_types:
        multiplier *= TYPE_EFFECTIVENESS.get((move_type, t), 1.0)
    return multiplier

def is_immune(move_type, target_types, move_category, move_name=""):
    if move_category == "Status":
        return False
    if move_name == "Bide":
        return False
    if move_name == "Seismic Toss":
        return False
    immunity_rules = {
        "Normal": ["Ghost"],
        "Ghost": ["Normal"],
        "Electric": ["Ground"],
        "Ground": ["Flying"],
        "Fighting": ["Ghost"],
        "Poison": ["Steel"],
        "Psychic": ["Dark"],
        "Dragon": ["Fairy"]
    }
    return any(t in immunity_rules.get(move_type, []) for t in target_types)