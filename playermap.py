import numpy as np

class npPlayerMap:
    def __init__(self):
        self.playerIndexes = {}
        self.playerPos = np.array([])
        self.dists = np.array([[]])

    def add(self, player):
        self.playerIndexes[player['id']] = len(self.playerPos)
        if self.playerPos.size > 0:
            self.playerPos = np.vstack((self.playerPos, [player['id'], *player['xy']]))
        else:
            self.playerPos = np.array([[player['id'], *player['xy']]])
        self.calcDists()

    def update(self, player):
        self.playerPos[self.playerIndexes[player['id']]][1:] = player['xy']
        self.calcDists()

    def remove(self, iD=None, player=None):
        iD = iD or player['id']
        index = self.playerIndexes[iD]
        del self.playerIndexes[iD]
        for iD, i in self.playerIndexes.items():
            if i > index:
                self.playerIndexes[iD] -= 1
        self.playerPos = np.vstack((self.playerPos[:index], self.playerPos[index+1:]))
        self.calcDists()

    def calcDists(self):
        X = self.playerPos[:, 1:]
        self.dists =  np.abs(X[:,np.newaxis] - X).max(axis=2)

    def get_within_range(self, player, dist=15):
        l = self.dists[self.playerIndexes[player['id']]]
        return [self.playerPos[i][0] for i, x in enumerate(l) if x <= dist]
