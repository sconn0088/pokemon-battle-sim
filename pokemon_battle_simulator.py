from constants import get_type_multiplier, is_immune
from utils import select_move
import random

def use_move(user, target, log, can_flinch=True):
    if user.current_move.multi_turn_type == "charge":
        user.must_charge = True
        user.multi_turn_move = user.current_move
        user.multi_turn_counter += 1
        if log: log.add(f"{user.name} began charging...")
        return
    
    if user.current_move.multi_turn_type == "invulnerable":
        user.invulnerable = True
        user.vulnerable_to = [m.strip() for m in user.current_move.vulnerable_to.split(",")] if user.current_move.vulnerable_to else []
        user.multi_turn_move = user.current_move
        user.multi_turn_counter = 1
        if log: log.add(f"{user.name} flew up high!" if user.current_move.name == "Fly" else f"{user.name} dug underground!")
        return
    
    if user.current_move.effect == "bide":
        # First time - set Bide
        if not user.is_biding:
            user.is_biding = True
            user.multi_turn_move = user.current_move
            min_turns, max_turns = map(int, user.current_move.duration.split("-"))
            num_turns = random.randint(min_turns, max_turns)
            user.multi_turn_counter = num_turns
            if log: log.add(f"{user.name} is biding its time...")
            return
        # After biding for a few turns - turn it off
        if user.is_biding:
            user.is_biding = False
    
    if log: log.add(f"{user.name} used {user.current_move.name}!")

    # Immunity check
    if is_immune(user.current_move.type, target.types, user.current_move.name):
        if log: log.add("It had no effect!")
        return

    # Accuracy vs Evasiveness stage adjustment
    accuracy_stage = user.stat_stages.get("accuracy", 0)
    evasiveness_stage = target.stat_stages.get("evasiveness", 0)

    accuracy_multiplier = get_stage_multiplier(accuracy_stage)
    evasiveness_multiplier = get_stage_multiplier(evasiveness_stage)

    adjusted_accuracy = user.current_move.accuracy * (accuracy_multiplier / evasiveness_multiplier)
    hit_roll = random.uniform(0, 100)

    if user.current_move.target == "self":
        adjusted_accuracy = 100
    
    if hit_roll > adjusted_accuracy:
        if log: log.add(f"{user.name}'s {user.current_move.name} missed!")
        return

    if user.current_move.effect == "skip":
        if log: log.add(f"But nothing happened!")
        return

    if user.current_move.effect == "crit_boost" and user.current_move.name == "Focus Energy":
        user.next_crit_boosted = True
        if log: log.add(f"{user.name} is getting pumped!")
        return
    
    if user.current_move.name == "Dream Eater" and target.status != "asleep":
        if log: log.add(f"{user.name}'s {user.current_move.name} missed!")
        return
    
    if user.current_move.effect == "counter":
        if user.last_move_received_category == "Physical" and user.last_damage_taken > 0:
            counter_damage = user.last_damage_taken * 2
            target.current_hp -= counter_damage
            if log: log.add(f"{target.name} took {counter_damage} damage!")
        else:
            if log: log.add(f"{user.name}'s Counter failed!")
        return

    damage = calculate_damage(user, target, log)

    if user.current_move.effect == "multi_hit":
        damage = multi_hit_attack(user, target, damage, log)
    
    apply_damage(damage, user, target, log)

    if user.current_move.effect in ["raise_stat", "lower_stat"]:
        apply_stat_stage_change(user, target, log)

    if user.current_move.effect == "flinch" and can_flinch:
        try_inflict_flinch(user, target, log)

    if user.current_move.multi_turn_type == "recharge":
        user.must_recharge = True
    
    if user.current_move.effect == "status":
        try_inflict_status(user, target, log)
    
    if user.current_move.effect == "confuse":
        try_inflict_confusion(user, target, log)
    
    if user.current_move.effect == "absorb":
        absorb_health(damage, user, log)
    
    if user.current_move.effect == "confuse_self":
        set_multi_turn_confuse_self(user)

def calculate_damage(user, target, log):
    if user.current_move.category in ["Physical", "Special"]:
        if user.current_move.category == "Physical":
            attack_stat = user.attack * get_stage_multiplier(user.stat_stages.get("attack", 0))
            if user.status == "burned":
                attack_stat = attack_stat // 2
                if log: log.add(f"{user.name}'s Attack is halved due to burn!")
            defense_stat = target.defense * get_stage_multiplier(target.stat_stages.get("defense", 0))
        else:
            attack_stat = user.special_attack * get_stage_multiplier(user.stat_stages.get("special_attack", 0))
            defense_stat = target.special_defense * get_stage_multiplier(target.stat_stages.get("special_defense", 0))

        if target.invulnerable and user.current_move.name not in target.vulnerable_to:
            if log: log.add(f"{target.name} is unaffected!")
            return 0
        
        # Check for critical hit
        is_crit = False
        crit_rate = 1/24
        if user.current_move.effect == "crit_boost" or user.next_crit_boosted:
            crit_rate = 1/8
            user.next_crit_boosted = False

        if random.random() < crit_rate:
            is_crit = True
            if log: log.add("A critical hit!")
        
        level_factor = (2 * user.level) / 5 + 2
        base_damage = (((level_factor * user.current_move.power * (attack_stat / defense_stat)) / 50) + 2)
        if is_crit:
            base_damage *= 2
        type_multiplier = get_type_multiplier(user.current_move.type, target.types)
        final_damage = int(base_damage * type_multiplier)
        
        if user.current_move.effect == "bide":
            final_damage = user.bide_damage * 2

        if log:
            if type_multiplier > 1:
                log.add("It's super effective!")
            elif type_multiplier < 1:
                log.add("It's not very effective...")
        return final_damage

def apply_damage(damage, user, target, log):
    if damage is None:
        damage = 0
    
    # Special case: Earthquake hitting Dig
    if target.invulnerable and user.current_move.name == "Earthquake":
        damage *= 2
        if log: log.add("Earthquake hits with double power during Dig!")
    
    target.current_hp -= damage

    if user.current_move.effect == "bide" and damage == 0:
        if log: log.add("But it failed!")

    if damage > 0:
        target.last_damage_taken = damage
        target.last_move_received_category = user.current_move.category # track Physical/Special
        if log: log.add(f"{target.name} took {damage} damage!")
    
    if target.is_biding:
        target.bide_damage += damage
    
    user.bide_damage = 0

def determine_turn_order(combatant_1, combatant_2):
    turn_order = [(combatant_2, combatant_1), (combatant_1, combatant_2)]

    if combatant_1.current_move.name == "Quick Attack" and combatant_2.current_move.name != "Quick Attack":
        turn_order = [(combatant_1, combatant_2), (combatant_2, combatant_1)]
    elif combatant_2.current_move.name == "Counter" and combatant_1.current_move.name != "Counter":
        turn_order = [(combatant_1, combatant_2), (combatant_2, combatant_1)]
    elif combatant_1.speed * get_stage_multiplier(combatant_1.stat_stages.get("speed", 0)) >= combatant_2.speed * get_stage_multiplier(combatant_2.stat_stages.get("speed", 0)):
        turn_order = [(combatant_1, combatant_2), (combatant_2, combatant_1)]
    return turn_order

##################################################
###############  BATTLE FUNCTIONS  ###############
##################################################

###############    STAT CHANGES    ###############
def apply_stat_stage_change(user, target, log):
    stat_name = user.current_move.stat

    if random.randint(1, 100) <= user.current_move.chance:
        change = user.current_move.stages
    
        if user.current_move.target == "self":
            current_stage = user.stat_stages[stat_name]
            # Check stat limits
            if user.current_move.effect == "raise_stat" and current_stage >= 6:
                if log: log.add(f"{user.name}'s {stat_name} won't go higher!")
                return
            # Check chance of effect
            new_stage = max(-6, min(6, current_stage + change))
            user.stat_stages[stat_name] = new_stage
            if log: log.add(f"{user.name}'s {stat_name} rose!")
        else:
            current_stage = target.stat_stages[stat_name]
            # Check stat limits
            if user.current_move.effect == "lower_state" and current_stage <= -6:
                if log: log.add(f"{target.name}'s {stat_name} won't go lower!")
                return
            # Check chance of effect
            new_stage = max(-6, min(6, current_stage - change))
            target.stat_stages[stat_name] = new_stage
            if log: log.add(f"{target.name}'s {stat_name} fell!")

def get_stage_multiplier(stage):
    stage_multipliers = {
        -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
         0: 2/2,
         1: 3/2, 2: 4/2, 3: 5/2, 4: 6/2, 5: 7/2, 6: 8/2
    }
    return stage_multipliers.get(stage, 1.0)

###############   STATUS CHANGES   ###############
def try_inflict_status(user, target, log):
    # Already afflicted
    if target.status != "OK":
        if user.current_move.chance < 100:
            return
        if log: log.add(f"{target.name} is already {target.status}!")
        return

    # Apply status based on chance
    if random.randint(1, 100) <= user.current_move.chance:
        # Type-based immunities
        status = user.current_move.status  # e.g., "burned", "paralyzed"
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
            min_turns, max_turns = map(int, user.current_move.duration.split('-'))
            target.sleep_turns = random.randint(min_turns, max_turns)
            if log: log.add(f"{target.name} fell asleep!")
            return
        if log: log.add(f"{target.name} was {status}!")

def try_inflict_confusion(user, target, log):
    if target.is_confused:
        if log: log.add(f"{target.name} is already confused!")
        return
    if random.randint(1, 100) <= user.current_move.chance:
        min_turns, max_turns = map(int, user.current_move.duration.split('-'))
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
def try_inflict_flinch(user, target, log):
    if user.current_move.effect == "flinch" and random.randint(1, 100) <= user.current_move.chance:
        target.flinched = True
        if log: log.add(f"{target.name} flinched!")

###############       ABSORB       ###############
def absorb_health(damage, user, log):
    if damage > 0:
        heal = int(damage * user.current_move.effect_value)
        user.current_hp = min(user.hp, user.current_hp + heal)
        if log: log.add(f"{user.name} recovered {heal} HP!")

###############    MULTI-ATTACK    ###############
def multi_hit_attack(user, target, damage, log):
    min_hits, max_hits = map(int, user.current_move.hits.split("-")) if "-" in user.current_move.hits else (int(user.current_move.hits), int(user.current_move.hits))
    num_hits = random.randint(min_hits, max_hits)
    total_damage = damage * num_hits
    # Check if Twineedle poisons opponent
    if hasattr(user.current_move, 'status') and user.current_move.status and hasattr(user.current_move, 'chance') and user.current_move.chance > 0:
        try_inflict_status(user, target, log)
    if damage > 0:
        if log: log.add(f"{user.current_move.name} hit {num_hits} times!")
    return total_damage

############ MULTI-TURN CONFUSE SELF #############
def set_multi_turn_confuse_self(user):
    # Set number of turns the attack will last
    user.multi_turn_move = user.current_move
    min_turns, max_turns = map(int, user.current_move.multi_turn.split("-"))
    num_turns = random.randint(min_turns, max_turns)
    user.multi_turn_counter = num_turns

def set_confusion_self(user, log):
    # User becomes confused after multi-turn attacks
    user.is_confused = True
    min_turns, max_turns = map(int, user.multi_turn_move.duration.split("-"))
    num_turns = random.randint(min_turns, max_turns)
    user.confused_turns = num_turns
    if log: log.add(f"{user.name} became confused!")
    user.multi_turn_move = None

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

        player.last_damage_taken = 0
        opponent.last_damage_taken = 0
        player.last_move_received_category = None
        opponent.last_move_received_category = None
        
        select_move(player)
        select_move(opponent)

        turn_order = determine_turn_order(player, opponent)

        for i, (acting_pokemon, defending_pokemon) in enumerate(turn_order):
            
            if acting_pokemon.is_fainted():
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
                    damage = calculate_damage(acting_pokemon, defending_pokemon, log)
                    apply_damage(damage, acting_pokemon, defending_pokemon, log)
                    continue

                if move_to_use.multi_turn_type == "invulnerable":
                    acting_pokemon.invulnerable = False
                    acting_pokemon.vulnerable_to = []
                    if log: log.add(f"{acting_pokemon.name} used {move_to_use.name}!")
                    acting_pokemon.multi_turn_move = None
                    damage = calculate_damage(acting_pokemon, defending_pokemon, log)
                    apply_damage(damage, acting_pokemon, defending_pokemon, log)
                    continue

                if move_to_use.effect == "confuse_self":
                    if log: log.add(f"{acting_pokemon.name}'s attack continues!")
                    damage = calculate_damage(acting_pokemon, defending_pokemon, log)
                    apply_damage(damage, acting_pokemon, defending_pokemon, log)
                    continue

                if move_to_use.effect == "bide":
                    if log: log.add(f"{acting_pokemon.name} is biding its time...")
                    continue
            
            if acting_pokemon.multi_turn_move and acting_pokemon.multi_turn_counter == 0:
                if acting_pokemon.multi_turn_move.effect == "confuse_self":
                    set_confusion_self(acting_pokemon, log)
                if acting_pokemon.multi_turn_move.effect == "bide":
                    acting_pokemon.current_move = acting_pokemon.multi_turn_move
                    acting_pokemon.multi_turn_move = None
            
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
            
            use_move(acting_pokemon, defending_pokemon, log, can_flinch=(i == 0))

            if defending_pokemon.is_fainted():
                log.add(f"{defending_pokemon.name} fainted!")
                log.add(f"{acting_pokemon.name} wins!")
                return acting_pokemon.name

        process_end_of_turn_status(player, log)
        process_end_of_turn_status(opponent, log)
