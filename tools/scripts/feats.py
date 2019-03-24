import logging
import sqlite3
from traceback import format_exc
from xml.etree import ElementTree as ET

from command import AbstractCommand

logger = logging.getLogger(__name__)


def processFeatElement(xml_elem):
    name = ""
    text = ""
    for feat_elem in xml_elem:
        if feat_elem.tag == "name":
            name = feat_elem.text
        elif feat_elem.tag == "text":
            if feat_elem.text:
                if text:
                    text = text + "\n" + feat_elem.text
                else:
                    text = feat_elem.text
        else:
            continue
    return {name: text}


def processFeatsFile(path_str):
    xml_file = ET.parse(path_str)
    root = xml_file.getroot()
    parsed_feats = {}
    for elem in root:
        if elem.tag == "feat":
            parsed_feats.update(processFeatElement(elem))
        else:
            continue
    return parsed_feats


def insertFeats(db_conn, parsed_feats):
    with db_conn:
        db_conn.executemany("INSERT INTO feats VALUES (?,?,?)", [(k.lower(), k, v) for k,v in parsed_feats.items()])
        logger.info(f"INSERTED <<{len(parsed_feats.keys())}>> rows into feats table")
        

class Feats(AbstractCommand):
    names = ["feats", "feat", "fts"]
    desc = "Parse feat files and fill feats table in db"

    def Run(self, db_conn, data_file):
        try:
            parsed_feats = processFeatsFile(data_file)
            insertFeats(db_conn, parsed_feats)
        except Exception:
            logger.error(f"Error parsing feats files\n{format_exc()}")
