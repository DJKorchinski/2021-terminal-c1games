from attackbase import AttackBase 
from algo_util import * 

class GutterAttack(AttackBase):
    LEFT = 0
    RIGHT = 1
    LEFT_GUTTER_WALL =build_diagonal([14,2],[3,13]) +\
        build_diagonal([14,2],[16,4]) + build_diagonal([16,4],[18,4])
    LEFT_GUTTER_PATH = build_diagonal([14,0],[17,3]) + build_diagonal([13,0],[1,12]) 
    LEFT_GUTTER_PATH = LEFT_GUTTER_PATH + [[loc[0],loc[1]+1] for loc in LEFT_GUTTER_PATH]
    LEFT_SCOUT_SPAWNS = [[17,3],[12,1]]
    LEFT_SCORING_SCOUT_SPAWN = [[17,3]]
    LEFT_DEST_SPAWN = [[8,5]]
    LEFT_BONUS_BUFF_REGION = [[13,2]]

    CENTRAL_BUFF_REGION = build_diagonal([13,7],[14,7])

    def __init__(self, config, mirror = False,addDemo = False):
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

        self.mirror = mirror 
        self.demolishers = addDemo
        self.path = GutterAttack.LEFT_GUTTER_PATH 
        self.wallpath = GutterAttack.LEFT_GUTTER_WALL
        self.scoutspawns = GutterAttack.LEFT_SCOUT_SPAWNS
        self.destspawn = GutterAttack.LEFT_DEST_SPAWN
        self.scoringscoutspawn = GutterAttack.LEFT_SCORING_SCOUT_SPAWN
        if(mirror):
            self.path = mirror_symmetry(self.path)
            self.wallpath = mirror_symmetry(self.wallpath)
            self.scoutspawns = mirror_symmetry(self.scoutspawns)
            self.destspawn = mirror_symmetry(self.destspawn)
            self.scoringscoutspawn = mirror_symmetry(self.scoringscoutspawn)

    def attackPossible(self,game_state):
        gs = game_state 
        possible = True
        SPcost = 0
        MPcost = 0
        

        #first, check if the walking path is clear.
        for loc in self.path: 
            if(not (gs.contains_stationary_unit(loc) is False)):
                return (False,0,0)
        
        #then, how much would it cost to build the up the attack? 
        #first, the essential "buffs"
        for loc in GutterAttack.CENTRAL_BUFF_REGION:
            unit = gs.contains_stationary_unit(loc)
            if(unit is False):
                SPcost+= gs.type_cost(SUPPORT,False)[0]
                SPcost+= gs.type_cost(SUPPORT,True)[0]
            elif(not unit.upgraded):
                SPcost+= gs.type_cost(SUPPORT,True)[0]
        #then, how much would it cost to build the wall?
        for loc in self.wallpath:
            unit = gs.contains_stationary_unit(loc)
            if(unit is False):
                SPcost+=gs.type_cost(WALL,False)[0]

        #finally, for this version, just use:
        if(self.demolishers):
            MPcost = 15
        else: 
            MPcost = 16
        #can we afford it, now that all is said and done? 
        possible = gs.get_resource(MP) >= MPcost and gs.get_resource(SP)>=SPcost
        
        #if we have surplus structure supplies 
        self.bonus_towers = 0 #storing how many wall segments we can convert into supports!
        self.bonus_tower_spots = []
        wall_seg_index = 0
        while(possible and SPcost > gs.get_resource(SP) - 6 and wall_seg_index < len(self.wallpath)): 
            #then maybe we should convert some of our structure points into extra supports, using the wall path. 
            #search for a spot along the wall path that is clear, and add it to the self.bonus_towers... 
            site = self.wallpath[wall_seg_index]
            unit = gs.contains_stationary_unit(site)
            if(unit is False):
                self.bonus_towers+=1
                self.bonus_tower_spots+=[site]
            SPcost += gs.type_cost(SUPPORT,False)[0]
            wall_seg_index+=1

        return (possible, SPcost,MPcost)
    
    def reservedSquares(self):
        return self.path 
    
    def spawnAttack(self,game_state):
        gs=game_state 
        gs.attempt_spawn(SUPPORT,GutterAttack.CENTRAL_BUFF_REGION)
        gs.attempt_upgrade(GutterAttack.CENTRAL_BUFF_REGION)
        if(self.bonus_towers > 0):
            gs.attempt_spawn(SUPPORT,self.bonus_tower_spots)
        gs.attempt_spawn(WALL,self.wallpath)
        
        #now to spawn the attack. 
        if(self.demolishers):
            gs.attempt_spawn(DEMOLISHER,self.destspawn,4)
            gs.attempt_spawn(SCOUT,self.scoringscoutspawn,100)
        else:
            gs.attempt_spawn(SCOUT,self.scoutspawns[1],8)
            gs.attempt_spawn(SCOUT,self.scoutspawns[0],100)