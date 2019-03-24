import logging
import sqlite3
from os import listdir
from traceback import format_exc
from os.path import join, isfile
import xml.etree.ElementTree as ET

from command import AbstractCommand

logger = logging.getLogger(__name__)

def parseSpellsFromFile(root):
    spells = [] 
    for spell in root:
        parsed_spell = {}
        for elem in spell:
            if elem.tag == 'name':
                parsed_spell['name'] = elem.text
                parsed_spell['url_name'] = elem.text.lower().replace(" ", "_").replace("'","")
            if elem.tag == 'roll':
                continue
            if elem.tag == 'text':
                if elem.text is not None:
                    if parsed_spell.get('text', None) is not None:
                        parsed_spell['text'] = parsed_spell['text'] + "\n\n" + elem.text
                    else:
                        parsed_spell['text'] = elem.text
            elif elem.tag == "duration":
                if "Concentration" in elem.text:
                    parsed_spell['concentration'] = "YES"
                else:
                    parsed_spell['concentration'] = "NO"
                parsed_spell[elem.tag] = elem.text
            else:
                parsed_spell[elem.tag]=elem.text
        if 'ritual' not in parsed_spell.keys():
            parsed_spell['ritual']="NO"
        spells.append(parsed_spell)
    return spells


def parseAllSpellFiles(data_folder):
    filesList = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
    path_str = [join(data_folder, i) for i in filesList]
    all_spells = []
    errors = []
    for path in path_str:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            spells = (parseSpellsFromFile(root))
            all_spells.extend(spells)
            logging.info(f"PARSED {len(spells)} SPELLS FROM {path}")
        except Exception:
            errors.append(f"Failed parsing file {path}\n{format_exc()}")
    return all_spells, errors


def insertSpells(db_conn, all_spells):
    keys = [
        'url_name',
        'name',
        'level', 
        'school',
        'time',
        'range',
        'components', 
        'duration',
        'concentration',
        'ritual',
        'classes',
        'text'
    ]
    with db_conn as conn:
        conn.executemany(
            "INSERT INTO spells VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(spell[key] for key in keys) for spell in all_spells]
        )
    logger.info(f"INSERTED <<{len(all_spells)}>> rows to spells table")

class Spells(AbstractCommand):
    names = ["spells", "spell", "spl"]
    desc = "Parse spells files and fill spells table in db"

    def Run(self, db_conn, data_folder):
        all_spells, errors = parseAllSpellFiles(data_folder) # kinda Golang like
        if not errors:
            insertSpells(db_conn, all_spells)
        else:
            logger.warn("SPELLS data not inserted due to errors")
            for err in errors:
                logger.error(err)
    