import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import numpy as np

from gutter_attack import GutterAttack
from algo_util import *

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        #building the attack suites: 
        self.attackSuite = [\
            GutterAttack(config,GutterAttack.LEFT),\
            GutterAttack(config,GutterAttack.RIGHT),
            GutterAttack(config,GutterAttack.RIGHT,True),
            GutterAttack(config,GutterAttack.RIGHT,True)
            ]
        self.lastAttack=None 

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        
        """

        #check for possible attacks: 
        possibilities = [attack.attackPossible(game_state) for attack in self.attackSuite]
        possibilities = [pos for pos in possibilities if pos[0]]
        #TODO: smarter decision making code about whether the attack is a good idea. 
        #for now, just take a random one, with a bias against the last one. 
        self.attacking = False  
        if(len(possibilities)>0):
            attack_index = random.randint(0,len(possibilities)-1)
            attack_choice = self.attackSuite[attack_index]
            if(attack_choice is self.lastAttack):
                #draw one more time, to encourage a different attack. 
                attack_index = random.randint(0,len(possibilities)-1)
                attack_choice = self.attackSuite[attack_index]
            self.attacking = True 
            self.lastAttack=attack_choice
        
        self.reserved_tiles = []
        if(self.attacking):
            self.reserved_tiles = attack_choice.reservedSquares()
            attack_choice.spawnAttack(game_state) 

        #now, build the great wall of defences. 
        # First, place essential defences:
        self.build_essential_defences(game_state)
        self.repair_simple_defences(game_state)

        #do we have too much money left over? 
        iter = 0
        while(game_state.get_resource(SP) > 20):
            #maybe perform some random upgrades or spam down more buffs or more turrets? 
            iter+=1
            total = 0
            total += self.build(game_state,build_diagonal([13,7],[14,7]),SUPPORT,True)
            total += self.build(game_state,build_diagonal([13,6],[14,6]),SUPPORT,True)
            if(total==0 or iter > 10):
                break

    def build(self,game_state,locs,unit,upgrade = False):
        #now, attempt to build: 
        filtered_locs = [loc for loc in locs if (not loc in self.reserved_tiles)]
        total = game_state.attempt_spawn(unit,filtered_locs)
        if(upgrade):
            total+=game_state.attempt_upgrade(filtered_locs)
        return total

    def build_essential_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        critical_turrets = [[3,12],[24,12],[11,8],[16,8]]
        self.build(game_state,critical_turrets,TURRET,True)        

        #build walls in order of priority: 
        # wall_rounds = [[[0,13],[3,13]],[[27,13],[24,13]],[[12,10],[16,10]],[[3,13],[11,10]],[[24,13],[16,10]] ] #sloping, smooth wall.
        wall_rounds = [[[0,13],[3,13]],[[27,13],[23,13]],[[9,9],[18,9]],[[4,12],[8,8]],[[23,12],[19,8]] ] #jagged wall, with traps.
        for round in wall_rounds:
            locs = build_diagonal(round[0],round[1])
            self.build(game_state,locs,WALL)

        #get a few extra turrets: 
        bonus_turrets = [[10,8],[17,8],[12,8],[15,8]]
        self.build(game_state,bonus_turrets,TURRET)

        #walls worth upgrading.
        critical_walls = [[pair[0],pair[1]+1] for pair in critical_turrets]+\
            [[0,13],[27,13]]
        game_state.attempt_upgrade(critical_walls)

        #upgrade the extra turrets: 
        bonus_turrets = [[10,8],[17,8],[12,8],[15,8]]
        self.build(game_state,bonus_turrets,TURRET,True)

    def build_support_structures(self, game_state):
        """
        Build the upgraded support structures using hardcoded locations.
        """
        total_upgraded_or_built = 0
        support_locations = [[13,8],[14,8],[12,8],[15,8]]
        for loc in support_locations:
            num_built=game_state.attempt_spawn(SUPPORT,loc)
            num_upgraded =game_state.attempt_upgrade(loc)
            total_upgraded_or_built+=(num_built+num_upgraded)
        return total_upgraded_or_built
            
    def gutterball_attack(self, game_state):
        """
        Build a wall to force an attack at one edge. 
        Send out scouts in two groups to attack (suicide bombing) that edge.
        """
        wall_locs = [ [x,15-x] for x in range(4,14)]
        wall_locs += [ [x,2] for x in range(14,17) ]
        gs=game_state
        gs.attempt_spawn(WALL,wall_locs)
        gs.attempt_spawn(SCOUT,[10,3],8)
        gs.attempt_spawn(SCOUT,[15,1],1000)


    def repair_simple_defences(self,game_state):
        """
        Re-build all up-upgraded units.
        """
        gs = game_state
        for y in range(0,gs.HALF_ARENA):
            for x in range(gs.HALF_ARENA-1-y,gs.HALF_ARENA+y+1):
                loc = [x,y]
                unit = gs.contains_stationary_unit(loc)
                if(unit is False):
                    continue 
                if(unit.upgraded):
                    if(unit.health > unit.max_health*.9):
                        continue 
                # if(unit.unit_type == SUPPORT):
                #     continue 
                gs.attempt_remove([x,y])
                # print(unit)
                # elif(unit.stationary and (not unit.upgraded)):
                #     gs.attempt_remove([x,y])

    # def build_reactive_defense(self, game_state):
    #     """
    #     This function builds reactive defenses based on where the enemy scored on us from.
    #     We can track where the opponent scored by looking at events in action frames 
    #     as shown in the on_action_frame function
    #     """
    #     for location in self.scored_on_locations:
    #         # Build turret one space above so that it doesn't block our own edge spawn locations
    #         build_location = [location[0], location[1]+1]
    #         game_state.attempt_spawn(TURRET, build_location)

    # def stall_with_interceptors(self, game_state):
    #     """
    #     Send out interceptors at random locations to defend our base from enemy moving units.
    #     """
    #     # We can spawn moving units on our edges so a list of all our edge locations
    #     friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
    #     # Remove locations that are blocked by our own structures 
    #     # since we can't deploy units there.
    #     deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
    #     # While we have remaining MP to spend lets send out interceptors randomly.
    #     while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
    #         # Choose a random deploy location.
    #         deploy_index = random.randint(0, len(deploy_locations) - 1)
    #         deploy_location = deploy_locations[deploy_index]
            
    #         game_state.attempt_spawn(INTERCEPTOR, deploy_location)
    #         """
    #         We don't have to remove the location since multiple mobile 
    #         units can occupy the same space.
    #         """

    # def demolisher_line_strategy(self, game_state):
    #     """
    #     Build a line of the cheapest stationary unit so our demolisher can attack from long range.
    #     """
    #     # First let's figure out the cheapest unit
    #     # We could just check the game rules, but this demonstrates how to use the GameUnit class
    #     stationary_units = [WALL, TURRET, SUPPORT]
    #     cheapest_unit = WALL
    #     for unit in stationary_units:
    #         unit_class = gamelib.GameUnit(unit, game_state.config)
    #         if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
    #             cheapest_unit = unit

    #     # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
    #     # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
    #     for x in range(27, 5, -1):
    #         game_state.attempt_spawn(cheapest_unit, [x, 11])

    #     # Now spawn demolishers next to the line
    #     # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
    #     game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    # def least_damage_spawn_location(self, game_state, location_options):
    #     """
    #     This function will help us guess which location is the safest to spawn moving units from.
    #     It gets the path the unit will take then checks locations on that path to 
    #     estimate the path's damage risk.
    #     """
    #     damages = []
    #     # Get the damage estimate each path will take
    #     for location in location_options:
    #         path = game_state.find_path_to_edge(location)
    #         damage = 0
    #         for path_location in path:
    #             # Get number of enemy turrets that can attack each location and multiply by turret damage
    #             damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
    #         damages.append(damage)
        
    #     # Now just return the location that takes the least damage
    #     return location_options[damages.index(min(damages))]

    # def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
    #     total_units = 0
    #     for location in game_state.game_map:
    #         if game_state.contains_stationary_unit(location):
    #             for unit in game_state.game_map[location]:
    #                 if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
    #                     total_units += 1
    #     return total_units
        
    # def filter_blocked_locations(self, locations, game_state):
    #     filtered = []
    #     for location in locations:
    #         if not game_state.contains_stationary_unit(location):
    #             filtered.append(location)
    #     return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        # state = json.loads(turn_string)
        # events = state["events"]
        # breaches = events["breach"]
        # for breach in breaches:
        #     location = breach[0]
        #     unit_owner_self = True if breach[4] == 1 else False
        #     # When parsing the frame data directly, 
        #     # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
        #     if not unit_owner_self:
        #         gamelib.debug_write("Got scored on at: {}".format(location))
        #         self.scored_on_locations.append(location)
        #         gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
