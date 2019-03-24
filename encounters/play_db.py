import sqlite3
import json
from datetime import datetime
from pprint import pprint

# this script inserts some mock players into the db
p1 = {
    "name": "TestPlayer1",
    "AC": 14, 
    "HP": 100, 
    "Stats":{"STR":10, "DEX":10, "CON":10, "INT":10, "WIS":10, "CHA":10},
    "Skills Proficient": ["History", "Investigation"],
    "Skills Expert": ["Arcana"],
    "Saving Throws Proficient": ["INT", "WIS"],
    "Class": {"Wizard": 5}
}
p2 = {"name": "TestPlayer2",
        "AC": 20, 
        "HP": 176, 
        "Stats":{"STR":19, "DEX":10, "CON":20, "INT":10, "WIS":15, "CHA":13},
        "Skills Proficient": ["History", "Perception"],
        "Skills Expert": ["Arcana"],
        "Saving Throws Proficient": ["STR", "CON"],
        "Class": {"Fighter": 8}
}

p3 = {"name": "TestPlayer3",
        "AC": 16, 
        "HP": 56, 
        "Stats":{"STR":10, "DEX":10, "CON":10, "INT":10, "WIS":10, "CHA":18},
        "Skills Proficient": ["History", "Investigation"],
        "Skills Expert": ["Arcana"],
        "Saving Throws Proficient": ["DEX", "CHA"],
        "Class": {"Bard": 8}
    }

p4 = {  "name": "DeadTestPlayer",
        "AC": 20, 
        "HP": 100, 
        "Stats":{"STR":10, "DEX":10, "CON":10, "INT":10, "WIS":10, "CHA":10},
        "Skills Proficient": ["History", "Investigation"],
        "Skills Expert": ["Arcana"],
        "Saving Throws Proficient": ["INT", "WIS"],
        "Class": {"Wizard": 5}
    }

if __name__ == "__main__":
    conn = sqlite3.connect("/home/ms/projects/dnd_tool/store/data.sqlite")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    now = str(datetime.now())
    insertStuff = [
        (p1.get("name", "empty"), now, json.dumps(p1), 1),
        (p2.get("name", "empty"), now, json.dumps(p2), 1),
        (p3.get("name", "empty"), now, json.dumps(p3), 1),
        (p4.get("name", "empty"), now, json.dumps(p4), 0),
    ]
    table = "players"
    c.execute("""INSERT INTO ? values (?,?,?,?)""", (table, insertStuff[0][0], insertStuff[0][1], insertStuff[0][2], insertStuff[0][3],))
    conn.commit()



    conn.close()
