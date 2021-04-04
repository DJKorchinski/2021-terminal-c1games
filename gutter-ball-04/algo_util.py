import numpy as np

def build_diagonal(loc1,loc2):
    dx = loc2[0]-loc1[0]
    dy = loc2[1]-loc1[1]
    locs = []
    if(np.abs(dx)>=np.abs(dy)):
        #then we should do the stepping in x.
        stepsign = 1 if dx>=0 else -1
        for step in range(0,np.abs(dx)+1):
            x = loc1[0] + step * stepsign
            y = int(round(dy * step / np.abs(dx) + loc1[1]))
            locs.append([x,y])
    else: 
        #then we should do the stepping in y: 
        stepsign = 1 if dy>=0 else -1
        for step in range(0,np.abs(dy)+1):
            y = loc1[1] + step*stepsign
            x = int(round(dx * step / np.abs(dy) + loc1[0]))
            locs.append([x,y])
    return locs 


ARENA_SIZE = 28 
HALF_ARENA_SIZE = 14
def mirror_symmetry(locs):
    #making it a list of locs, even if it's just the one loc: 
    if(type(locs[0]) ==int):
        locs = [locs]
    newlocs = [ [ARENA_SIZE - loc[0] - 1,loc[1]] for loc in locs]
    return newlocs 