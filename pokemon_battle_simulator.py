from constants import get_type_multiplier, is_immune
from utils import select_move
import random, copy

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
    
    if user.disabled_move == user.current_move:
        if log: log.add(f"{user.name}'s {user.disabled_move.name} is disabled!")
        return
    
    if log: log.add(f"{user.name} used {user.current_move.name}!")

    if user.current_move.effect == "transform":
        transform(user, target, log)
        return
    
    if user.current_move.effect == "mimic":
        mimic_move(user, target, log)
        return

    # Immunity check
    if is_immune(user.current_move.type, target.types, user.current_move.category, user.current_move.name):
        if log: log.add("It had no effect!")
        return

    # Accuracy vs Evasiveness stage adjustment
    accuracy_stage = user.stat_stages.get("accuracy", 0)
    evasiveness_stage = target.stat_stages.get("evasiveness", 0)

    accuracy_multiplier = get_stage_multiplier(accuracy_stage)
    evasiveness_multiplier = get_stage_multiplier(evasiveness_stage)

    adjusted_accuracy = user.current_move.accuracy * (accuracy_multiplier / evasiveness_multiplier)
    hit_roll = random.uniform(0, 100)

    if user.current_move.target == "self" or user.current_move.effect == "swift":
        adjusted_accuracy = 100
    
    if hit_roll > adjusted_accuracy:
        if log: log.add(f"{user.name}'s {user.current_move.name} missed!")
        if user.current_move.name == "Jump Kick" or user.current_move.name == "High Jump Kick":
            user.current_hp -= 1
            if log: log.add(f"{user.name} kept going and crashed!")
            if log: log.add(f"{user.name} lost 1 health.")
        if user.current_move.effect == "rage_mode":
            user.is_enraged = False
            user.multi_turn_move = None
            user.stat_stages["attack"] = 0
        return

    if user.current_move.effect == "conversion":
        conversion(user, target, log)
        return
    
    if user.current_move.effect == "ohko":
        target.current_hp = 0
        return
    
    if user.current_move.effect == "leech_seed":
        leech_seed(user, target, log)
        return
    
    if user.current_move.effect == "mist":
        mist(user, log)
        return
    
    if user.current_move.effect == "heal":
        heal(user, log)
        return
    
    if user.current_move.effect == "skip":
        if log: log.add(f"But nothing happened!")
        return
    
    if user.current_move.effect == "clear_stats":
        haze(user, target, log)
        return

    if user.current_move.effect == "crit_boost" and user.current_move.name == "Focus Energy":
        if user.next_crit_boosted:
            user.next_crit_boosted = False
            if log: log.add("But it failed!")
        else:
            user.next_crit_boosted = True
            if log: log.add(f"{user.name} is getting pumped!")
        return
    
    if user.current_move.name == "Dream Eater" and target.status != "asleep":
        if log: log.add(f"{user.name}'s {user.current_move.name} missed!")
        return
    
    if user.current_move.effect == "disable":
        disable_move(user, target, log)
        return
    
    if user.current_move.effect == "rest":
        rest(user, log)
        return
    
    if user.current_move.effect == "counter":
        if user.last_move_received_category == "Physical" and user.last_damage_taken > 0:
            counter_damage = user.last_damage_taken * 2
            target.current_hp -= counter_damage
            if log: log.add(f"{target.name} took {counter_damage} damage!")
        else:
            if log: log.add(f"{user.name}'s Counter failed!")
        return

    if user.current_move.effect == "mirror_move":
        mirror_move(user, target, log)

    if user.current_move.effect == "screen":
        screen_defense(user, log)
        return
    
    if user.current_move.effect == "rage_mode":
        if not user.is_enraged:
            user.is_enraged = True
            user.multi_turn_move = user.current_move
    
    damage = calculate_damage(user, target, log)
    
    apply_damage(damage, user, target, log)

    if user.current_move.effect == "selfdestruct":
        user.current_hp = 0
        return
    
    if user.current_move.effect == "recoil":
        recoil(user, damage, log)

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
    
    if user.current_move.effect == "drain":
        absorb_health(damage, user, log)
    
    if user.current_move.effect == "confuse_self":
        set_multi_turn_confuse_self(user)

def calculate_damage(user, target, log):
    if user.current_move.effect == "bide":
        damage = user.bide_damage * 2
        return damage
    elif user.current_move.effect == "fixed_damage":
        if user.current_move.name == "Dragon Rage":
            damage = 40
        elif user.current_move.name == "Sonic Boom":
            damage = 20
        return damage
    elif user.current_move.effect == "level_scale":
        if user.current_move.name == "Psywave":
            damage_multiplier = random.randint(100, 150)
            damage = int((user.level * damage_multiplier) / 100)
        else:
            damage = user.level
        return damage
    elif user.current_move.effect == "super_fang":
        if target.current_hp == 1:
            damage = 1
        else:
            damage = int(target.current_hp / 2)
        return damage
    else:
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
            if target.light_screen_turns > 0 and user.current_move.category == "Special":
                base_damage = int(base_damage // 2)
            if target.reflect_turns > 0 and user.current_move.category == "Physical":
                base_damage = int(base_damage // 2) 
            type_multiplier = get_type_multiplier(user.current_move.type, target.types)
            final_damage = int(base_damage * type_multiplier)

            if user.current_move.effect == "multi_hit":
                final_damage = multi_hit_attack(user, target, final_damage, log)

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

    # Special case: Rage
    if damage > 0:
        if target.is_enraged:
            if target.stat_stages["attack"] < 6:
                target.stat_stages["attack"] += 1
                if log: log.add(f"{target.name}'s rage is building!")

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
            # Check if target covered by Mist
            if target.mist_turns > 0:
                if log: log.add(f"{target.name} is protected by Mist!")
                return
            # Check stat limits
            if user.current_move.effect == "lower_stat" and current_stage <= -6:
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

def mist(user, log):
    if user.mist_turns > 0:
        if log: log.add("But it failed!")
        return
    user.mist_turns = 5
    if log: log.add(f"{user.name} was shrouded in mist...")

def haze(user, target, log):
    user.is_seeded = False
    user.seeding_opponent = None
    target.is_seeded = False
    target.seeding_opponent = None
    for stat in user.stat_stages:
        user.stat_stages[stat] = 0
    for stat in target.stat_stages:
        target.stat_stages[stat] = 0
    if log: log.add("All stats were reset.")

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
        # Special case: Tri Attack
        if user.current_move.name == "Tri Attack":
            status = random.choice(["burned", "paralyzed", "frozen"])
        else:
            status = user.current_move.status # e.g., "burned", "paralyzed"
        
        # Type-based immunities
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
        if log: log.add(f"{pokemon.name} is hurt by poison and loses {damage} health!")
    elif pokemon.status == "badly poisoned":
        damage = max(1, int(pokemon.hp * 0.0625 * pokemon.toxic_counter))
        pokemon.current_hp -= damage
        pokemon.toxic_counter += 1
        if log: log.add(f"{pokemon.name} is hurt by Toxic and loses {damage} health!")
    elif pokemon.status == "burned":
        damage = max(1, pokemon.hp // 16)
        pokemon.current_hp -= damage
        if log: log.add(f"{pokemon.name} is hurt by its burn and loses {damage} health!")
    
    if pokemon.is_seeded and pokemon.seeding_opponent and not pokemon.is_fainted():
        leech_damage = max(1, pokemon.hp // 16)
        pokemon.current_hp -= leech_damage
        # Heal opponent, unless fainted
        opponent = pokemon.seeding_opponent
        if not opponent.is_fainted():
            opponent.current_hp = min(opponent.hp, opponent.current_hp + leech_damage)
            if log: log.add(f"{pokemon.name} is sapped by Leech Seed and loses {leech_damage} health!")
            if log: log.add(f"{opponent.name} recovered {leech_damage} health from Leech Seed!")
    
    if pokemon.disabled_turns > 0:
        pokemon.disabled_turns -= 1
        if pokemon.disabled_turns == 0:
            pokemon.disabled_move = None
            if log: log.add(f"{pokemon.name} is disabled no more!")
    
    if pokemon.mist_turns > 0:
        pokemon.mist_turns -= 1
        if pokemon.mist_turns == 0:
            if log: log.add("The mist faded away...")
    
    if pokemon.light_screen_turns > 0:
        pokemon.light_screen_turns -= 1
        if pokemon.light_screen_turns == 0:
            if log: log.add("Light Screen faded away...")
    
    if pokemon.reflect_turns > 0:
        pokemon.reflect_turns -= 1
        if pokemon.reflect_turns == 0:
            if log: log.add("Reflect faded away...")

###############     LEECH SEED     ###############
def leech_seed(user, target, log):
    if "Grass" in target.types:
        if log: log.add(f"{target.name} is immune to Leech Seed!")
        return
    target.is_seeded = True
    target.seeding_opponent = user
    if log: log.add(f"{target.name} was seeded!")

###############       FLINCH       ###############
def try_inflict_flinch(user, target, log):
    if user.current_move.effect == "flinch" and random.randint(1, 100) <= user.current_move.chance:
        target.flinched = True
        if log: log.add(f"{target.name} flinched!")

###############       DRAIN        ###############
def absorb_health(damage, user, log):
    if damage > 0:
        heal = int(damage * user.current_move.effect_value)
        user.current_hp = min(user.hp, user.current_hp + heal)
        if log: log.add(f"{user.name} recovered {heal} health!")

###############       RECOIL       ###############
def recoil(user, damage, log):
    recoil_damage = int(user.current_move.effect_value * damage)
    user.current_hp -= recoil_damage
    if log: log.add(f"{user.name} was hit with recoil!")
    if log: log.add(f"{user.name} took {recoil_damage} damage.")

###############        REST        ###############
def rest(user, log):
    user.status = "asleep"
    user.sleep_turns = int(user.current_move.duration)
    user.current_hp = user.hp
    if log: log.add(f"{user.name} went to sleep!")
    if log: log.add(f"{user.name} recovered all health!")

###############       RECOVER      ###############
def heal(user, log):
    if user.current_hp == user.hp:
        if log: log.add("But it failed!")
        return
    recover_health = int(user.hp * user.current_move.effect_value)
    user.current_hp = min(user.hp, user.current_hp + recover_health)
    if log: log.add(f"{user.name} recovered health!")

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

###############      TRANSFORM     ###############
def transform(user, target, log):
    if user.transformed:
        if log: log.add("But it failed!")
        return
    
    # Set a transform flag
    user.transformed = True
    
    # Copy stats (except current HP)
    user.attack = target.attack
    user.defense = target.defense
    user.special_attack = target.special_attack
    user.special_defense = target.special_defense
    user.speed = target.speed

    # Copy stat stages
    user.stat_stages = target.stat_stages.copy()

    # Copy types
    user.types = target.types[:]

    # Copy move list
    user.moves = [copy.deepcopy(move) for move in target.moves]

    if log: log.add(f"{user.name} transformed into {target.name}!")

###############     CONVERSION     ###############
def conversion(user, target, log):
    user.types = [target.types[0]]
    if log: log.add(f"{user.name} converted to the {target.types[0]} type!")

###############       MIMIC        ###############
def mimic_move(user, target, log):
    # Find the index of the current move
    mimic_index = None
    for i, move in enumerate(user.moves):
        if move.name == "Mimic":
            mimic_index = i
            break
    if mimic_index is not None:
        copied_move = copy.deepcopy(random.choice(target.moves))
        user.moves[mimic_index] = copied_move
        if log: log.add(f"{user.name} copied {copied_move.name}!")

###############    MIRROR MOVE     ###############
def mirror_move(user, target, log):
    # Fails if the user attacks first
    user_speed = user.speed * get_stage_multiplier(user.stat_stages.get("speed", 0))
    target_speed = target.speed * get_stage_multiplier(target.stat_stages.get("speed", 0))
    if user_speed > target_speed:
        if log: log.add("But it failed!")
        return
    # Fails if the user was not hit with an attack
    if not hasattr(user, 'last_move_received') or user.last_move_received is None:
        if log: log.add("But it failed!")
        return
    mirrored = user.last_move_received
    user.current_move = mirrored
    if log: log.add(f"{user.name} used {mirrored.name}!")

###############      DISABLE       ###############
def disable_move(user, target, log):
    if target.disabled_move:
        if log: log.add("But it failed!")
        return
    target.disabled_move = random.choice(target.moves)
    min_turns, max_turns = map(int, user.current_move.duration.split("-"))
    num_turns = random.randint(min_turns, max_turns)
    target.disabled_turns = num_turns
    if log: log.add(f"{target.name}'s {target.disabled_move.name} was disabled!")

###############       SCREEN       ###############
def screen_defense(user, log):
    if user.light_screen_turns > 0 or user.reflect_turns > 0:
        if log: log.add("But it failed!")
        return
    if user.current_move.name == "Light Screen":
        user.light_screen_turns = 5
        if log: log.add("Damage from special attacks is reduced!")
    elif user.current_move.name == "Reflect":
        user.reflect_turns = 5
        if log: log.add("Damage from physical attacks is reduced!")

##################################################
###############       BATTLE       ###############
##################################################
def simulate_battle(player, opponent, log):
    while True:
        if player.is_fainted() and opponent.is_fainted():
            log.add(f"Both {player.name} and {opponent.name} fainted!")
            log.add("It's a tie! No winner")
            return "No winner"
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
            
            if acting_pokemon.is_enraged:
                acting_pokemon.current_move = acting_pokemon.multi_turn_move
            
            use_move(acting_pokemon, defending_pokemon, log, can_flinch=(i == 0))

            acting_pokemon.last_move_used = acting_pokemon.current_move
            defending_pokemon.last_move_received = acting_pokemon.current_move

            if acting_pokemon.current_move.effect == "selfdestruct" or acting_pokemon.current_move.effect == "ohko":
                break

            if defending_pokemon.is_fainted():
                log.add(f"{defending_pokemon.name} fainted!")
                log.add(f"{acting_pokemon.name} wins!")
                return acting_pokemon.name

        process_end_of_turn_status(player, log)
        process_end_of_turn_status(opponent, log)
