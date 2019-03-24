class Encounter:
    
    def __init__(self, name, players: dict):
        self.turnNumber = 1
        self.encounterName = name
        self.currentPlayerIndex = 0
        self.currentPlayerName = "" 
        self.allPlayers = players    # name[players.Player]
        self.initiativeOrder = [] # [name...]
    
    def setInitiativeOrder(self):
        inits = [(k,v.initiative) for k,v in self.allPlayers.items()]
        inits.sort(key = lambda x: x[1], reverse=True)
        self.initiativeOrder = [i[0] for i in inits]
        if self.currentPlayerName == "":
            self.currentPlayerName = self.initiativeOrder[0]
    
    def setPlayersInitiatives(self, names_inits):
        # names_inits == tuple of names and initiatives
        # [(Ricciardo, 3),...]
        try:
            for player, initiative in names_inits:
                self.allPlayers[player].setInitiative(initiative)
        except Exception as e:
            print(f"Error setting initiative\n{e}")
    
    def swapPlayersInInitiativeOrder(self, name1, name2):
        try:
            pos1 = self.initiativeOrder.index(name1)
            pos2 = self.initiativeOrder.index(name2)
            self.initiativeOrder[pos1] = name2
            self.initiativeOrder[pos2] = name1
        except ValueError as e:
            print(f"Error swapping players in initiative order\n{e}")

    def addPlayer(self, name, player):
        self.allPlayers[name] = player

    def removePlayer(self, name):
        if name in self.allPlayers.keys():
            del self.allPlayers[name]
    
    def nextPlayer(self):
        nextIndex = self.currentPlayerIndex + 1
        while True:
            if nextIndex == len(self.initiativeOrder):
                self.turnNumber+=1
                nextIndex = 0
            if self.allPlayers[self.initiativeOrder[nextIndex]].status in ["conscious", "unconscious"]:
                self.currentPlayerIndex = nextIndex
                self.currentPlayerName = self.initiativeOrder[nextIndex]
                break
            nextIndex+=1

    def toJSON(self):
        pass
    
    def persistToDB(self, db):
        pass

    def damagePlayers(self, points, players_affected:list):
        # players_hit is a list of strings (names)
        for player in players_affected:
            self.allPlayers[player].damageOrHealPlayer(-points)

    def healPlayers(self, points, players_affected: list):
        for player in players_affected:
            self.allPlayers[player].damageOrHealPlayer(points)
        
    def addTempHP(self, points, players_affected: list):
        for player in players_affected:
            self.allPlayers[player].addTempHP(points)

