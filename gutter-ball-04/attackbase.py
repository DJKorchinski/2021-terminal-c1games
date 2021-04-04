

class AttackBase(object):
    def __init__(self,gs):
        self.gs = gs 
        pass 
    
    def attackPossible(self,game_state):
        """
        Should return a tuple (bool,int,int), being (attack possible, attack SP cost, attack MP cost)
        """
    
    def reservedSquares(self,game_state):
        """
        Computes the reserved tiles for our attack. 
        """

    def spawnAttack(self,game_state_):
        """
        Builds the units necessary for the attack!
        """
        