import json
import logging
import sqlite3
from collections import defaultdict
from traceback import format_exc
from xml.etree import ElementTree as ET

from command import AbstractCommand

logger = logging.getLogger(__name__)

def processTraitElements(xml_elem):
    trait_name = ""
    text = ""
    for trait_elem in xml_elem:
        if trait_elem.tag == "name":
            trait_name = trait_elem.text
        elif trait_elem.tag == "text":
            if trait_elem.text:
                if text:
                    text = text + "\n" + trait_elem.text
                else:
                    text = trait_elem.text
        else:
            continue
    return {trait_name: text}


def processDetailElements(xml_elem):
    return {xml_elem.tag: xml_elem.text}


def processRaceElements(xml_elem):
    race_name = ""
    details = {}
    traits = defaultdict(str)
    for subelem in xml_elem:
        if subelem.tag == "name":
            race_name = subelem.text
        elif subelem.tag == "trait":
            traits.update(processTraitElements(subelem))
        else:
            details.update(processDetailElements(subelem))
    details.update({"traits": dict(traits)})
    return {race_name: details}


def processRacesFile(path_str):
    xml_file = ET.parse(path_str)
    root = xml_file.getroot()
    parsed_races = {}
    for elem in root:
        if elem.tag == "race":
            parsed_races.update(processRaceElements(elem))
        else:
            continue
    return parsed_races


def _makeUrlName(race_name):
    return race_name.lower().replace("(", " ").\
        replace(")","").replace("  ", " ").\
            replace(" ", "_").replace("-", "_")


def _getRaceName(string):
    stripped_str = string.rstrip()
    race_name = ""
    indx = stripped_str.find(" ")
    if indx > 0:
        race_name = stripped_str[:indx]
    else:
        race_name = stripped_str
    return race_name


def _formatSubRace(string):
    return string.rstrip(" ").replace("  "," ").replace("(", ": ").replace(")","").replace(" :", ":")


def insertData(conn, parsed_data):
    with conn:
        # url_name: str, name: str, featues: str(json serializable)
        conn.executemany("INSERT INTO races VALUES (?,?,?,?)", [
            (
                _makeUrlName(k),
                _formatSubRace(k),
                _getRaceName(k),
                json.dumps(v)
            ) 
            for k,v in parsed_data.items()
            ]
        )
        logger.info(f"INSERTED <<{len(parsed_data)}>> rows into races table")


class Races(AbstractCommand):
    names = ["races", "race", "rcs"]
    desc = "Parse races files and fill races table in db"

    def Run(self, db_conn, data_file):
        try:
            parsed_races = processRacesFile(data_file)
            insertData(db_conn, parsed_races)
        except Exception:
            logger.error(f"Error parsing races file\n{format_exc()}")
