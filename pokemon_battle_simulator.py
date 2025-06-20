from constants import get_type_multiplier
from utils import select_move
import random

def use_move(user, target, move, log, can_flinch=True):
    if move.multi_turn_type == "charge":
        user.must_charge = True
        user.multi_turn_move = move
        user.multi_turn_counter += 1
        if log: log.add(f"{user.name} began charging...")
        return
    
    if move.multi_turn_type == "invulnerable":
        user.invulnerable = True
        user.vulnerable_to = [m.strip() for m in move.vulnerable_to.split(",")] if move.vulnerable_to else []
        user.multi_turn_move = move
        user.multi_turn_counter = 1
        if log: log.add(f"{user.name} flew up high!" if move.name == "Fly" else f"{user.name} dug underground!")
        return
    
    if log: log.add(f"{user.name} used {move.name}!")

    # Accuracy vs Evasiveness stage adjustment
    accuracy_stage = user.stat_stages.get("accuracy", 0)
    evasiveness_stage = target.stat_stages.get("evasiveness", 0)

    accuracy_multiplier = get_stage_multiplier(accuracy_stage)
    evasiveness_multiplier = get_stage_multiplier(evasiveness_stage)

    adjusted_accuracy = move.accuracy * (accuracy_multiplier / evasiveness_multiplier)
    hit_roll = random.uniform(0, 100)

    if move.target == "self":
        adjusted_accuracy = 100
    
    if hit_roll > adjusted_accuracy:
        if log: log.add(f"{user.name}'s {move.name} missed!")
        return

    if move.effect == "skip":
        if log: log.add(f"But nothing happened!")
        return

    if move.effect == "crit_boost" and move.name == "Focus Energy":
        user.next_crit_boosted = True
        if log: log.add(f"{user.name} is getting pumped!")
        return
    
    if move.name == "Dream Eater" and target.status != "asleep":
        if log: log.add(f"{user.name}'s {move.name} missed!")
        return

    damage = calculate_damage(user, target, move, log)

    if move.effect == "multi_hit":
        damage = multi_hit_attack(target, move, damage, log)

    apply_damage(damage, target, move, log)

    if move.effect in ["raise_stat", "lower_stat"]:
        apply_stat_stage_change(user, target, move, log)

    if move.effect == "flinch" and can_flinch:
        try_inflict_flinch(target, move, log)

    if move.multi_turn_type == "recharge":
        user.must_recharge = True
    
    if move.effect == "status":
        try_inflict_status(target, move, log)
    
    if move.effect == "confuse":
        try_inflict_confusion(target, move, log)
    
    if move.effect == "absorb":
        absorb_health(damage, user, move, log)

def calculate_damage(user, target, move, log):
    if move.category in ["Physical", "Special"]:
        if move.category == "Physical":
            attack_stat = user.attack * get_stage_multiplier(user.stat_stages.get("attack", 0))
            if user.status == "burned":
                attack_stat = attack_stat // 2
                if log: log.add(f"{user.name}'s Attack is halved due to burn!")
            defense_stat = target.defense * get_stage_multiplier(target.stat_stages.get("defense", 0))
        else:
            attack_stat = user.special_attack * get_stage_multiplier(user.stat_stages.get("special_attack", 0))
            defense_stat = target.special_defense * get_stage_multiplier(target.stat_stages.get("special_defense", 0))

        if target.invulnerable and move.name not in target.vulnerable_to:
            if log: log.add(f"{target.name} is unaffected!")
            return 0
        
        # Check for critical hit
        is_crit = False
        crit_rate = 1/24
        if move.effect == "crit_boost" or user.next_crit_boosted:
            crit_rate = 1/8
            user.next_crit_boosted = False

        if random.random() < crit_rate:
            is_crit = True
            if log: log.add("A critical hit!")
        
        level_factor = (2 * user.level) / 5 + 2
        base_damage = (((level_factor * move.power * (attack_stat / defense_stat)) / 50) + 2)
        if is_crit:
            base_damage *= 2
        type_multiplier = get_type_multiplier(move.type, target.types)
        final_damage = int(base_damage * type_multiplier)
        
        if log:
            if type_multiplier > 1:
                log.add("It's super effective!")
            elif type_multiplier < 1:
                log.add("It's not very effective...")
        return final_damage

def apply_damage(damage, target, move, log):
    if damage is None:
        damage = 0
    
    # Special case: Earthquake hitting Dig
    if target.invulnerable and move.name == "Earthquake":
        damage *= 2
        if log: log.add("Earthquake hits with double power during Dig!")
    
    target.current_hp -= damage
    if damage > 0:
        if log: log.add(f"{target.name} took {damage} damage!")

##################################################
###############  BATTLE FUNCTIONS  ###############
##################################################

###############    STAT CHANGES    ###############
def apply_stat_stage_change(user, target, move, log):
    # Determine the correct target
    target_pokemon = user if move.target == "self" else target
    stat_name = move.stat

    current_stage = target_pokemon.stat_stages[stat_name]

    # Check stat limits
    if move.effect == "raise_stat" and current_stage >= 6:
        if log: log.add(f"{target_pokemon.name}'s {stat_name} won't go higher!")
        return
    elif move.effect == "lower_stat" and current_stage <= -6:
        if log: log.add(f"{target_pokemon.name}'s {stat_name} won't go lower!")
        return

    # Check chance of effect
    if random.randint(1, 100) <= move.chance:
        change = move.stages if move.effect == "raise_stat" else -move.stages
        new_stage = max(-6, min(6, current_stage + change))
        target_pokemon.stat_stages[stat_name] = new_stage
        if change >= 1:
            if log: log.add(f"{target_pokemon.name}'s {stat_name} rose!")
        elif change <= -1:
            if log: log.add(f"{target_pokemon.name}'s {stat_name} fell!")

def get_stage_multiplier(stage):
    stage_multipliers = {
        -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
         0: 2/2,
         1: 3/2, 2: 4/2, 3: 5/2, 4: 6/2, 5: 7/2, 6: 8/2
    }
    return stage_multipliers.get(stage, 1.0)

###############   STATUS CHANGES   ###############
def try_inflict_status(target, move, log):
    # Already afflicted
    if target.status != "OK":
        if move.chance < 100:
            return
        if log: log.add(f"{target.name} is already {target.status}!")
        return

    # Apply status based on chance
    if random.randint(1, 100) <= move.chance:
        # Type-based immunities
        status = move.status  # e.g., "burned", "paralyzed"
        if status == "burned" and "Fire" in target.types:
            if log: log.add(f"{target.name} is immune to burn!")
            return
        if status == "paralyzed" and "Electric" in target.types:
            if log: log.add(f"{target.name} is immune to paralysis!")
            return
        if status == "poisoned" and ("Poison" in target.types or "Steel" in target.types):
            if log: log.add(f"{target.name} is immune to poison!")
            return
        if status == "frozen" and "Ice" in target.types:
            if log: log.add(f"{target.name} is immune to freeze!")
            return
        
        target.status = status
        if status == "paralyzed":
            target.speed = max(1, target.speed // 4)
            if log: log.add(f"{target.name} was paralyzed!")
            if log: log.add(f"{target.name}'s speed fell due to paralysis!")
            return
        if status == "badly poisoned":
            target.toxic_counter = 1
            if log: log.add(f"{target.name} was badly poisoned!")
            return
        if status == "asleep":
            min_turns, max_turns = map(int, move.duration.split('-'))
            target.sleep_turns = random.randint(min_turns, max_turns)
            if log: log.add(f"{target.name} fell asleep!")
            return
        if log: log.add(f"{target.name} was {status}!")

def try_inflict_confusion(target, move, log):
    if target.is_confused:
        if log: log.add(f"{target.name} is already confused!")
        return
    if random.randint(1, 100) <= move.chance:
        min_turns, max_turns = map(int, move.duration.split('-'))
        target.is_confused = True
        target.confused_turns = random.randint(min_turns, max_turns)
        if log: log.add(f"{target.name} became confused!")

############## CHECK STATUS EFFECTS ##############
def check_confusion(pokemon, log):
    if pokemon.is_confused:
        pokemon.confused_turns -= 1
        if pokemon.confused_turns <= 0:
            pokemon.is_confused = False
            if log: log.add(f"{pokemon.name} snapped out of confusion!")
            return False
        if random.random() < 0.5:
            damage = int(((((2*pokemon.level/5 + 2)*pokemon.attack*40)/pokemon.defense)/50) + 2)
            pokemon.current_hp -= damage
            if log: log.add(f"{pokemon.name} hurt itself in its confusion!")
            if log: log.add(f"{pokemon.name} took {damage} damage!")
            return True
    return False

def check_sleep(pokemon, log):
    if pokemon.status == "asleep":
        if pokemon.sleep_turns > 0:
            pokemon.sleep_turns -= 1
            if log: log.add(f"{pokemon.name} is fast asleep.")
            return True
        else:
            pokemon.status = "OK"
            if log: log.add(f"{pokemon.name} woke up!")
            return False
    return False

def check_paralysis(pokemon, log):
    if pokemon.status == "paralyzed":
        if random.randint(1, 100) <= 25:
            if log: log.add(f"{pokemon.name} is fully paralyzed and can't move!")
            return True  # turn is skipped
    return False

def check_freeze(pokemon, log):
    if pokemon.status == "frozen":
        if log: log.add(f"{pokemon.name} is frozen solid and can't move!")
        return True  # Skip turn
    return False

def process_end_of_turn_status(pokemon, log):
    if pokemon.status == "poisoned":
        damage = max(1, pokemon.hp // 8)
        pokemon.current_hp -= damage
        if log: log.add(f"{pokemon.name} is hurt by poison and loses {damage} HP!")
    elif pokemon.status == "badly poisoned":
        damage = max(1, int(pokemon.hp * 0.0625 * pokemon.toxic_counter))
        pokemon.current_hp -= damage
        pokemon.toxic_counter += 1
        if log: log.add(f"{pokemon.name} is hurt by Toxic and loses {damage} HP!")
    elif pokemon.status == "burned":
        damage = max(1, pokemon.hp // 16)
        pokemon.current_hp -= damage
        if log: log.add(f"{pokemon.name} is hurt by its burn and loses {damage} HP!")

###############       FLINCH       ###############
def try_inflict_flinch(target, move, log):
    if move.effect == "flinch" and random.randint(1, 100) <= move.chance:
        target.flinched = True
        if log: log.add(f"{target.name} flinched!")

###############       ABSORB       ###############
def absorb_health(damage, user, move, log):
    if damage > 0:
        heal = int(damage * move.effect_value)
        user.current_hp = min(user.hp, user.current_hp + heal)
        if log: log.add(f"{user.name} recovered {heal} HP!")

###############    MULTI-ATTACK    ###############
def multi_hit_attack(target, move, damage, log):
    min_hits, max_hits = map(int, move.hits.split("-")) if "-" in move.hits else (int(move.hits), int(move.hits))
    num_hits = random.randint(min_hits, max_hits)
    total_damage = damage * num_hits
    # Check if Twineedle poisons opponent
    if hasattr(move, 'status') and move.status and hasattr(move, 'chance') and move.chance > 0:
        try_inflict_status(target, move, log)
    if log: log.add(f"{move.name} hit {num_hits} times!")
    return total_damage

##################################################
###############       BATTLE       ###############
##################################################
def simulate_battle(player, opponent, log):
    while True:
        if player.is_fainted():
            log.add(f"{player.name} fainted!")
            log.add(f"{opponent.name} wins!")
            return opponent.name
        if opponent.is_fainted():
            log.add(f"{opponent.name} fainted!")
            log.add(f"{player.name} wins!")
            return player.name

        if player.speed * get_stage_multiplier(player.stat_stages.get("speed", 0)) >= opponent.speed * get_stage_multiplier(opponent.stat_stages.get("speed", 0)):
            turn_order = [(player, opponent), (opponent, player)]
        else:
            turn_order = [(opponent, player), (player, opponent)]

        for i, (acting_pokemon, defending_pokemon) in enumerate(turn_order):
            if acting_pokemon.is_fainted():
                continue

            if check_confusion(acting_pokemon, log):
                continue
            if check_sleep(acting_pokemon, log):
                continue
            if check_paralysis(acting_pokemon, log):
                continue
            if check_freeze(acting_pokemon, log):
                continue
            if acting_pokemon.flinched:
                acting_pokemon.flinched = False
                continue

            if acting_pokemon.must_recharge:
                if log: log.add(f"{acting_pokemon.name} must recharge and can't move!")
                acting_pokemon.must_recharge = False
                continue
            
            if acting_pokemon.multi_turn_move and acting_pokemon.multi_turn_counter > 0:
                acting_pokemon.multi_turn_counter -= 1
                move_to_use = acting_pokemon.multi_turn_move

                if move_to_use.multi_turn_type == "charge":
                    if log: log.add(f"{acting_pokemon.name} used {move_to_use.name}!")
                    acting_pokemon.multi_turn_move = None
                    damage = calculate_damage(acting_pokemon, defending_pokemon, move_to_use, log)
                    apply_damage(damage, defending_pokemon, move_to_use, log)
                    continue

                if move_to_use.multi_turn_type == "invulnerable":
                    acting_pokemon.invulnerable = False
                    acting_pokemon.vulnerable_to = []
                    if log: log.add(f"{acting_pokemon.name} used {move_to_use.name}!")
                    acting_pokemon.multi_turn_move = None
                    damage = calculate_damage(acting_pokemon, defending_pokemon, move_to_use, log)
                    apply_damage(damage, defending_pokemon, move_to_use, log)
                    continue
            
            move = select_move(acting_pokemon)
            # can_flinch is True only for the first Pokémon in the turn_order
            use_move(acting_pokemon, defending_pokemon, move, log, can_flinch=(i == 0))

            if defending_pokemon.is_fainted():
                log.add(f"{defending_pokemon.name} fainted!")
                log.add(f"{acting_pokemon.name} wins!")
                return acting_pokemon.name

        process_end_of_turn_status(player, log)
        process_end_of_turn_status(opponent, log)
