from pprint import pprint
import sqlite3
from enconunter import Encounter
from players import LoadPlayerFromDb


"""THIS IS A BASIC INITIATIVE TRACKER DEMO"""


if __name__ == "__main__":
    p_names = ["aarakocra", "werebat", "scaladar", "dragonclaw"]
    names_inits = [("aarakocra", 24), ("werebat", 10), ("scaladar", 11), ("dragonclaw", 19)]
    db = sqlite3.connect("/home/ms/projects/dnd_tool/store/data.sqlite")
    real_players = {k:LoadPlayerFromDb(db, k) for k in p_names}
    _longest_name = max(list(map(len, [i.name for i in real_players.values()]))) # just for print formatting
    
    print("## BEFORE SETTING INITIATIVES##\n||      NAME      || HP || INIT ||")
    for p in real_players.values():
        print('    ', p.name.ljust(4, " "), str(p.fullHP).rjust(_longest_name-len(p.name)+8, " "), str(p.initiative).rjust(5, " "))
    
    e = Encounter("simpleTest", real_players)
    e.setPlayersInitiatives(names_inits)
    e.setInitiativeOrder()
    print()
    
    print("## AFTER SETTING INITIATIVES ##\n||      NAME      || HP || INIT ||")
    for p in real_players.values():
        print('    ', p.name.ljust(4, " "), str(p.fullHP).rjust(_longest_name-len(p.name)+8, " "), str(p.initiative).rjust(5, " "))
    
    print()
    print("## INITIATIVE ORDER ##\n", e.initiativeOrder)
    print()
    
    print("## SIMULATE TAKING TURNS ##")
    print("turn:", e.turnNumber,"index:", e.currentPlayerIndex, "name:", e.currentPlayerName)
    for i in range(0,10):
        e.nextPlayer()
        print("turn:", e.turnNumber, "index:", e.currentPlayerIndex, "name:", e.currentPlayerName)