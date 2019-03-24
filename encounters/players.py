import json
from sqlite3 import Error
from properties import Skills
import traceback

def LoadPlayerFromDb(db_conn, player_name, is_pc=False):
    # NOTE lazy coding galore
    if is_pc:
        with db_conn:
            try: 
                query_result = db_conn.execute("SELECT json_str FROM players WHERE title = ?", (player_name,))
                data_tuple = query_result.fetchone()
                if data_tuple is None:
                    raise ValueError("Provided player name does not match any known player names")
                data = json.loads(data_tuple[0])
                return PC(data["Title"], **data) 
            except Exception:
                raise Error(f"Error loading player\n{traceback.format_exc()}")
    with db_conn:
        try:
            query_result = db_conn.execute("SELECT full_desc_json FROM bestiary WHERE name = ?", (player_name,))
            data_tuple = query_result.fetchone()
            if data_tuple is None:
                raise ValueError(f"Provided beast or NPC name ||{player_name}|| does not match any known names")
            data = json.loads(data_tuple[0])
            return NPC(data["Name"], **data)
        except Exception:
            raise Error(f"Error loading player\n{traceback.format_exc()}")


class PlayerBaseClass:
    def __init__(self, name, fullhp, ac, status="conscious"):
        self.name = name
        self.status = status
        self.initiative = 0
        self.fullHP = fullhp
        self.currHP = fullhp
        self.AC = ac
        self.conditions = []

    def damageOrHealPlayer(self, amount):
        # provide negative amount for dmg dealt
        self.currHP = self.currHP + amount
        if self.currHP < 1:
            self.status = "dead"
        else:
            self.status = "conscious"
    
    def resetHP(self):
        self.currHP = self.fullHP
    
    def changeCurrHP(self, new_currenthp):
        self.currHP = new_currenthp

    def changeFullHP(self, new_fullhp):
        self.fullHP = new_fullhp
        if self.currHP > new_fullhp:
            self.currHP = new_fullhp
    
    def setInitiative(self, initiative):
        self.initiative = initiative

    def __str__(self):
        return f'"name": {self.name}\n"status": {self.status}\n"initiative": {self.initiative}\n"currHP": {self.currHP}\n"AC":{self.AC}\n"condition": {self.conditions }\n'


class PC(PlayerBaseClass):
    def __init__(self, name, **kwargs):
        self.stabile = True
        self.conditionImmune = kwargs.get('Condition Immunities')
        self.damageImmune = kwargs.get('Damage Immunities')
        self.damageResistant = kwargs.get('Damage Resistances')
        self.damageVulnerable = kwargs.get('Damage Vulnerabilities')
        self.languages = kwargs.get('Languages')
        self.savingThrows = {}
        self.skills = {}
        self.skillsProficient = kwargs.get("Skills Proficient")
        self.skillsExpert = kwargs.get("Skills Expert")
        self.savingThrowsProficient = kwargs.get("Saving Throws Proficient")
        self.speed = kwargs.get("Speed")
        self.size = kwargs.get("Size")
        self.stats = kwargs.get("Stats")
        self.statMods = {}
        self.tools = kwargs.get("Tools")
        self.gameClass = kwargs.get("Class")
        self._calcStats()
        self.tempHP = 0
        super().__init__(name, kwargs.get("HP"), kwargs.get("AC"))
    
    def setLevel(self, game_class, lvl):
        # TODO HANDLE ERRS IN HERE
        self.gameClass[game_class] = lvl
        self._calcStats()
        
    def setStat(self, stat, value):
        self.stats[stat] = value
        self._calcStats()
    
    def _calcStats(self):
        self._calcModifiers()
        self._calcSkills()
        self._calcSavingThrows()

    def _calcSkills(self):
        for k,v in Skills.items():
            for skill in v:
                if skill in self.skillsProficient:
                    self.skills[skill] = self.profBonus + self.statMods[k]
                elif skill in self.skillsExpert:
                    self.skills[skill] = self.profBonus*2 + self.statMods[k]
                else:
                    self.skills[skill] = self.statMods[k]

    def _calcSavingThrows(self):
            for k,v in self.statMods.items():
                if k in self.savingThrowsProficient:
                    self.savingThrows[k] = v + self.profBonus
                else:
                    self.savingThrows[k] = v
                    
    def _calcModifiersHelper(self, num):
        mod = 0
        if num > 9:
            mod = int(round((num-10)/2, 0))
        else:
            if num % 2 == 0:
                mod = -int((10-num)/2)
            else:
                mod = -int((10-num+1)/2)
        return mod

    def _calcModifiers(self):
        self.statMods = {k:self._calcModifiersHelper(v) for k,v in self.stats.items()}
    
    @property
    def playerClass(self):
        string = ""
        for k,v in self.gameClass.items():
            string = string + " " + str(k) + "(" + str(v) + ")" + "/"
        string.rstrip("/")
        return string
    
    @property
    def playerLvl(self):
        return sum([val for val in self.gameClass.values()])
    
    @property
    def profBonus(self):
        if self.playerLvl < 5:
            return 2
        elif self.playerLvl < 9:
            return 3
        elif self.playerLvl < 13:
            return 4
        elif self.playerLvl < 17:
            return 5
        else:
            return 6
    
    def damageOrHealPlayer(self, amount):
        # overcomplicated 
        # refactor into 2 clean functions: heal and damage
        leftoverAmount = 0
        if amount < 0:
            if self.tempHP > 0:
                if abs(amount) >= self.tempHP:
                    leftoverAmount = self.tempHP + amount
                    self.tempHP = 0
            else:
                leftoverAmount = amount
        else:
            leftoverAmount = amount
        self.currHP = self.currHP + leftoverAmount
        if self.currHP > self.fullHP:
            self.currHP = self.fullHP
        if self.currHP < 1:
            if self.currHP <= -self.fullHP:
                self.status = "dead"
            else:
                self.currHP = 0
                self.status = "unconscious"
                self.stabile = False
        else:
            if self.status == "unconscious":
                self.currHP = 1
            self.status = "conscious"
            self.stabile = True
    
    def addTempHP(self, amount):
        self.tempHP = amount
               
    def __str__(self):
        return f'"name": {self.name}\n"status": {self.status}\n"initiative":{self.initiative}\n"fullHP": {self.fullHP}\n"currHP": {self.currHP}\n"AC":{self.AC}\n'


class NPC(PlayerBaseClass):
    # NOTE I'm lazy
    def __init__(self, name, **kwargs):
        required_keys = ("AC", "HP", "Title", "Actions")
        for i in required_keys:
            if i not in kwargs.keys():
                kwargs[i] = None
        super().__init__(name, kwargs.pop("HP"), kwargs.pop("AC"))
        self.__dict__.update((k, v) for k,v in kwargs.items())

    
if __name__ == "__main__":
    # minimal test
    from pprint import pprint
    argss = {
        "AC": 20, 
        "HP": 100, 
        "Stats":{"STR":10, "DEX":10, "CON":10, "INT":10, "WIS":10, "CHA":10},
        "Skills Proficient": ["History", "Investigation"],
        "Skills Expert": ["Arcana"],
        "Saving Throws Proficient": ["INT", "WIS"],
        "Class": {"Wizard": 5}
    }
    p = PC("testName", **argss)
    print("PLAYER STATS:\n", p)
    pprint([p.savingThrows, p.skills, p.stats, p.statMods, p.profBonus])
        

    print("## TEST DAMAGE AND HEALS FROM HP 100 ##")
    p.damageOrHealPlayer(-32)
    print("HP&STATUS AFTER 32 DMG:", p.currHP, p.status)
    
    p.currHP = p.fullHP
    p.damageOrHealPlayer(-131)  
    print("HP&STATUS AFTER 100 DMG:", p.currHP, p.status)
    
    p.currHP = p.fullHP
    p.damageOrHealPlayer(-200)
    print("HP&STATUS AFTER 200 DMG:", p.currHP, p.status)

    p.currHP = p.fullHP
    p.damageOrHealPlayer(-32)
    print("HP&STATUS AFTER 32 DMG:", p.currHP, p.status)

    p.damageOrHealPlayer(-168)
    print("HP&STATUS AFTER 168 DMG (68 hp remaining):", p.currHP, p.status) # shoud be instadead

    p.currHP = p.fullHP
    p.damageOrHealPlayer(-32)
    print("HP&STATUS AFTER 32 DMG:", p.currHP, p.status)
    p.damageOrHealPlayer(11)
    print("HP&STATUS AFTER 11 HEAL:", p.currHP, p.status)

    print("#"*50 + "\n")
    print("## TESTING STABILIZING ##")
    p.currHP = p.fullHP
    p.damageOrHealPlayer(-112)
    print("### HP&STATUS&STABILE AFTER 112 DMG:\n", p.currHP, p.status, p.stabile)
    p.damageOrHealPlayer(11)
    print("### HP&STATUS&STABIILE AFTER 11 HEAL:\n", p.currHP, p.status, p.stabile)
    print("#"*50)
    p.currHP = p.fullHP
    p.addTempHP(10)
    print("## DEALING 12 DMG TO 100 HP and 10 TEMP:")
    p.damageOrHealPlayer(-12)
    print("HP | TEMP\n", p.currHP, p.tempHP)
