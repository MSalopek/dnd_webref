import json
import logging
import sqlite3
from os import listdir
from os.path import join, isfile
from traceback import format_exc

from command import AbstractCommand

logger = logging.getLogger(__name__)

def _handleTags(string):
    commaPos = [pos for pos, char in enumerate(string) if char == ","]
    tags = []
    # keep it simple stupid - this is always the same in my files
    tags.append(string[7:commaPos[0]])
    tags.append(string[commaPos[0]+2: commaPos[1]])
    tags.append(string[commaPos[1]+2: commaPos[2]])
    tags.append(string[commaPos[2]+2: len(string)-2])
    return tags 


def _handleSpeed(string):
    speeds = [i.lstrip() for i in string.rstrip()[10:].split(",")]
    speeds_dict = {}
    speeds_dict["base"] = speeds[0]
    for elem in speeds[1:]:
        for index, char in enumerate(elem):
            if not char.isalpha():
                speeds_dict[elem[:index]] = elem[index+1:]
                break
    return speeds_dict


def _handleScores(string):
    clean_str = string[2:].rstrip("|\n").replace(" ", "").split("|")
    stat_tuples = []
    for i in clean_str:
        parts = i.split("(")
        stat_tuples.append((parts[0], parts[1].rstrip(")")))
    return stat_tuples


def _collectNamesFromFile(search_path: str, file_name_str):
    names = []
    line_count = 1
    with open(join(search_path, file_name_str), "r") as f:
        for line in f:
            if line_count == 8 or line_count == 9:  # skip short description
                line_count += 1
                continue
            if line.startswith("**"):
                if line[2] == "*":
                    line_count += 1
                    continue
                split_line = line.lstrip("*").split("**")
                name = split_line[0].replace("*", "")
                names.append(name)
                line_count += 1
                continue
            line_count += 1
    return names


def collectAllNames(search_path: str, files: list):
    allNames = []
    for file_name in files:
        allNames.extend(_collectNamesFromFile(search_path, file_name))
    return allNames


def _parseBasicInfoLine(line_count: int, line: str, elements: dict):
    if line_count == 3:
        full_name = line.rstrip()[7:].replace('"',"")
        elements["Full Name"] = full_name
        elements["Name"] = line.rstrip()[7:].replace('"',"").replace(" ", "_").lower()
    elif line_count == 5:
        # example line -> tags: [gargantuan, dragon, cr24, monster-manual]
        tags = _handleTags(line)
        elements["Size"] = tags[0]
        elements["Type"] = tags[1]
        elements["Rating"] = tags[2][2:]
        elements["Source"] = tags[3]
    elif line_count == 8:
        elements["Short Description"] = line[2:line.rfind(",")] 
        elements["Alignment"] = line[line.rfind(",")+2:len(line)-3]
    elif line_count == 10:
        # '19 (natural armor)' # NOTE i'm trusting there's always a "("
        ac_n_type = line.rstrip()[16:]
        par_indx = ac_n_type.find("(")
        if par_indx < 0:
            elements["AC"] = int(ac_n_type)
            elements["AC Type"] = "undefined"
        else:
            elements["AC"] = int(ac_n_type[:par_indx-1])
            elements["AC Type"] = ac_n_type[par_indx+1:len(ac_n_type)-1]
    elif line_count == 12:
        hp_dice_str = line.rstrip()[15:].replace(" ", "")
        par_indx = hp_dice_str.find("(")
        if par_indx < 0:
            elements["HP"] = int(hp_dice_str) 
            elements["HP Dice"] = "undefined"       
        else:
            elements["HP"] = int(hp_dice_str[0:par_indx]) 
            elements["HP Dice"] = hp_dice_str[par_indx+1:len(hp_dice_str)-1]
    elif line_count == 14:
        elements["Speed"] = _handleSpeed(line)        
    elif line_count == 18:
        stat_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        score_tuples = _handleScores(line)
        elements["Stats"] = {stat_names[i]: int(score_tuples[i][0]) for i in range(len(stat_names))}
        elements["statMods"] = {stat_names[i]: int(score_tuples[i][1]) for i in range(len(stat_names))}


def _parseTraitsLine(line: str, elements: dict):
    if line[2].isalpha():
        name_n_text = line.rstrip().lstrip("**").split("** ")
        if name_n_text[0] == "Saving Throws":
            elements["Saving Throws"] = {k:int(v) for k,v in [i.split() for i in name_n_text[1].split(",")]}
        elif name_n_text[0] == "Skills":
            # reason for .rsplit() are multi word skill names
            # ["Sleight of Hand +4", "Animal Handling +1", "Perception +8"]
            elements["Skills"] = {k:int(v) for k,v in [i.rsplit(" ", 1) for i in name_n_text[1].split(",")]}
        else:
            elements[name_n_text[0]] = name_n_text[1].split(", ")        
    else:
        name_n_text = line.rstrip().lstrip("**").split("*** ")
        elements["Traits"][name_n_text[0]] = name_n_text[1]


def _parseExtraInfoLine(line: str, elements: dict, signals: dict):
    if line.rstrip() == "**Actions**":
        signals["actions_signal"] = 1
    elif line.rstrip() == "**Legendary Actions**":
        signals["actions_signal"] = 0
        signals["legendary_actions_signal"] = 1        
    elif "Spellcasting" in line:
        signals["spellcasting_signal"] = 1
        name_n_text = line.lstrip("***").split("*** ")
        elements["Spellcasting"] = name_n_text[1]
    elif signals["actions_signal"]:
        if not line[2].isalpha():
            name_n_text = line.rstrip().lstrip("***").split("*** ")
            elements["Actions"][name_n_text[0].rstrip(".")] = name_n_text[1]
    elif signals["legendary_actions_signal"]:
        if not line[2].isalpha():
            name_n_text = line.rstrip().lstrip("***").split("*** ")
            elements["Legendary Actions"][name_n_text[0].rstrip(".")] = name_n_text[1]                        
    elif signals["spellcasting_signal"]:
        if line.startswith("**"):
            signals["spellcasting_signal"] = 0
            _parseTraitsLine(line, elements)
        else:
            if len(line) > 1:
                text = line.lstrip("*").lstrip()
                elements["Spellcasting"] = elements["Spellcasting"] + text
    else:
        # if text not under actions/legendary actions/spellcasting
        _parseTraitsLine(line, elements)


def processFile(search_path, file_name_str):
    line_count = 1
    elements = {}
    elements["Traits"] = {}
    elements["Actions"] = {}
    elements["Legendary Actions"] = {}
    signals = {}
    signals["actions_signal"] = 0
    signals["legendary_actions_signal"] = 0
    signals["spellcasting_signal"] = 0
    with open(join(search_path, file_name_str), "r") as f:
        for line in f:
            if line_count < 19:
                _parseBasicInfoLine(line_count, line, elements)
                line_count += 1
            else:
                if line[0]=="*":
                    _parseExtraInfoLine(line, elements, signals)           
                line_count += 1
    return elements


def processAllFiles(_SEARCH_PATH, filesList, conn):
    errors = []
    dataToInsert = []
    for fileStr in filesList:
        try:
            processedFileDict = processFile(_SEARCH_PATH, fileStr)
            dataToInsert.append(processedFileDict)
            logger.info(f"PARSED BESTIARY FILE: {fileStr}")
        except Exception:
            errors.append((fileStr, format_exc()))
    return dataToInsert, errors


def insertData(conn, data):
    with conn:
        try:
            conn.executemany("INSERT INTO bestiary VALUES (?, ?, ?, ?, ?, ?, ?)", 
                [(i["Name"], i["AC"], i["HP"], i["Size"], i["Rating"], i["Alignment"], json.dumps(i)) for i in data])
            logger.info(f"INSERTED <<{len(data)}>> rows to bestiary table")
        except sqlite3.Error:
            logger.error(f"ERROR saving to bestiary\n{format_exc()}")


class Bestiary(AbstractCommand):
    names = ["bestiary", "beasts", "bst"]
    desc = "Parse bestiary files and fill bestiary table in db"

    def Run(self, db_conn, data_folder):
        filesList = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
        parsed, errors = processAllFiles(data_folder, filesList, db_conn)
        if not errors:
            try:
                insertData(db_conn, parsed)
            except Exception:
                logger.error(f"Error parsing bestiary data\n{format_exc()}")
        else:
            logger.warn("Bestiary data not inserted due to errors")
            for err in errors:
                logger.error(err)
