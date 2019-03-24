import logging
from os import listdir
from json import dumps as dumps
from traceback import format_exc
from os.path import join, isfile
from collections import defaultdict, OrderedDict
import xml.etree.ElementTree as etree

from .config import getConfig
from command import AbstractCommand

logger = logging.getLogger(__name__)


class ParsingError(Exception):
    pass


class OrderedDefaultDict(OrderedDict):
    factory = dict

    def __missing__(self, key):
        self[key] = value = self.factory()
        return value


def ProcessClassXML(path_str):
    tree = etree.parse(path_str)
    root = tree.getroot()
    parsed_file_dict = {"starting_features":{}}
    for _class in root:
        for elem in _class:
            if elem.attrib.get("level", False):
                parsed_file_dict[int(elem.attrib["level"])] = parseLevelFeatures(elem)
            else:
                insertStartingFeatures(elem, parsed_file_dict)
    return parsed_file_dict


def insertStartingFeatures(xml_element, result_dict_reference):
    if xml_element.tag == "items_choice":
        items = ""
        for sub_elem in xml_element:
            if items:
                items = items + "\n" + sub_elem.text
            else:
                items = sub_elem.text
        result_dict_reference["starting_features"]["starting_items"] = items
    else:
        result_dict_reference["starting_features"][xml_element.tag] = xml_element.text


def parseLevelFeatures(xml_element):
    levelFeatures = defaultdict(dict)
    for sub_elem in xml_element:
        if sub_elem.tag == "feature":
            if sub_elem.attrib.get('subclass', False):
                subclassName = sub_elem.attrib["subclass"]
                try:
                    subclassFeatureName, subclassFeatureTxt = parseFeatureNameAndText(sub_elem)
                    levelFeatures[subclassName][subclassFeatureName] = subclassFeatureTxt
                except Exception:
                    logger.error(f"Error during parsing <<SUBCLASS FEATURE>>\n{format_exc()}")
            else:
                try:
                    featureName, featureTxt = parseFeatureNameAndText(sub_elem)
                    if levelFeatures.get(featureName, False):
                        # if exists append to existing text
                        oldText = levelFeatures[featureName]
                        levelFeatures[featureName] = oldText + "\n" + featureTxt
                    else:
                        levelFeatures[featureName] = featureTxt
                except Exception:
                    logger.error(f"Error during parsing <<FEATURE>>\n{format_exc()}")
        else:
            levelFeatures[sub_elem.tag] = sub_elem.text
    return dict(levelFeatures) # freezes defaultdict 


def parseFeatureNameAndText(feature_element):
    featureName = ""
    featureTxt = ""
    for feature_element_child in feature_element:
        if feature_element_child.tag == "name":
            featureName = feature_element_child.text
        elif feature_element_child.tag == "text":
            if feature_element_child.text is None:
                featureTxt = featureTxt + "\n"
            else:
                if featureTxt:
                    featureTxt = featureTxt + "\n" + feature_element_child.text
                else:
                    featureTxt = feature_element_child.text
        else:
            raise ParsingError(f"Found unknown tag <<{feature_element_child.tag}>> while parsing sub-element <<{feature_element.tag}>>.")
    return featureName, featureTxt


def getFeaturesForLevel(parsed_file_dict, config, class_name, subclass, level) -> str:
    dict_to_jsonize = {}
    for key in parsed_file_dict.keys():
        if type(key) == int:
            if key <= level:
                if parsed_file_dict[key].get(subclass, False):
                    dict_to_jsonize.update(parsed_file_dict[key].get(subclass))
                else:
                    dict_to_jsonize.update(getUniqueSubClassFeatures(parsed_file_dict[key], config.CLASS_FEATURE_FILTER[class_name]['unique']))
                if key == level:
                    for i in config.CLASS_FEATURE_FILTER[class_name]['shared']:
                        dict_to_jsonize[i] = parsed_file_dict[level][i]
        else:
            dict_to_jsonize.update(parsed_file_dict[key])
    return dict_to_jsonize


def prepareDictForDBInsert(dictionary, config, class_name, subclass, level):
    url_name = config.TRANSLATE_NAMES_TO_URL_NAMES[class_name.upper()][subclass]
    return (url_name, class_name, subclass, level, dumps(dictionary))


def getUniqueSubClassFeatures(dictionary, ignore_set):
    uniqueFeatures = {}
    for k,v in dictionary.items():
        if k not in ignore_set:
            uniqueFeatures[k] = v
    return uniqueFeatures


def processAllClassFiles(path_to_folder):
    config = getConfig()
    filePathsList = [join(path_to_folder, f) for f in listdir(path_to_folder) if isfile(join(path_to_folder, f))]
    dbInsertData = [] # tuples
    for file_path in filePathsList:
        logger.info(f"PARSING FILE: {file_path}")
        parsed_file = ProcessClassXML(file_path)
        class_name = parsed_file['starting_features']['name'].upper()
        # class name contained in the parsed file dict
        for subclass in config.CLASS_FEATURE_FILTER[class_name]['unique']:
            for level in range(1, 21):
                dictToPrepare = getFeaturesForLevel(parsed_file, config, class_name, subclass, level)
                dbInsertData.append(prepareDictForDBInsert(dictToPrepare, config, class_name, subclass, level))
    return dbInsertData


def insertClassData(conn, data_to_insert):
    with conn:
        try:
            conn.executemany("INSERT INTO classes VALUES (?, ?, ?, ?, ?)", data_to_insert)
            row = conn.execute("SELECT count(*) FROM classes").fetchone()
            logger.info(f"INSERTED <<{row[0]}>> rows into classes table")
        except Exception:
            logger.error(f"ERROR INSERTING DATA\n{format_exc()}")


def alterProcessAllClassFiles(path_to_folder):
    config = getConfig()
    filePathsList = [join(path_to_folder, f) for f in listdir(path_to_folder) if isfile(join(path_to_folder, f))]
    dbInsertData = [] # tuples
    for file_path in filePathsList:
        logger.info(f"ALTER PARSING FILE: {file_path}")
        dbInsertData.append(alterProcessClassXML(file_path)) # tuple[4]
    return dbInsertData


def alterProcessClassXML(file_path):
    tree = etree.parse(file_path)
    root = tree.getroot()
    table_data = OrderedDefaultDict()
    base_features_data = OrderedDefaultDict()
    subclass_data = OrderedDefaultDict()
    for _class in root:
        for elem in _class:
            table_data_dict = {}
            if elem.attrib.get("level", False):
                if elem.attrib["level"] == "0":
                    for subelem in elem:
                        _name,_text = parseFeatureNameAndText(subelem)
                        base_features_data[_name] = _text
                    continue
                for subelem in elem:
                    if subelem.tag == "feature":
                        if subelem.attrib.get("subclass", False):
                            subclass_name = subelem.attrib["subclass"]
                            _name, _text = parseFeatureNameAndText(subelem)
                            subclass_data[subclass_name][_name] = _text
                        else:
                            _name, _text = parseFeatureNameAndText(subelem)
                            base_features_data[_name] = _text  
                    if subelem.tag == "slots":
                        table_data_dict[subelem.tag] = subelem.text.replace(',0', ',-').split(",")  
                    else:
                        if subelem.tag != "feature":
                            table_data_dict[subelem.tag] = subelem.text
                table_data[int(elem.attrib["level"])] = table_data_dict
            else:
                base_features_data[elem.tag] = elem.text
    col_names = list(list(table_data.values())[0].keys())
    # transform class data
    # using list of tuples to preserve ordering by level
    transformed_subclass_data = {}
    for key,val in subclass_data.items():
        transformed_subclass_data[key] = list(val.items())
    return (col_names, table_data, base_features_data, transformed_subclass_data)


def insertAlterClassData(conn, data):
    with conn:
        try:
            for class_tuples in data:
                url_name = class_tuples[2]['name'].lower()
                cls_name = url_name.upper()
                ready_data = (url_name, cls_name, *(dumps(i) for i in class_tuples))
                conn.execute("""INSERT INTO classes_alter 
                                    VALUES (?,?,?,?,?,?)""", ready_data)
        except Exception:
            logger.error(f"ERROR INSERTING ALTER CLASS DATA\n{format_exc()}")


class Classes(AbstractCommand):
    names = ["classes", "class", "cls"]
    desc = "Parse class files and fill classes table in db" 

    def Run(self, db_conn, data_folder):
        try:
            preparedData = processAllClassFiles(data_folder)
            insertClassData(db_conn, preparedData)
        except Exception:
            logger.error(f"Error parsing class files\n{format_exc()}")


class ClassesAlternative(AbstractCommand):
    names = ["classes_alter", "cls_alter"]
    desc = "Parse class files and fill classes_alter table in db.\nUses alternative parsing style."
    
    def Run(self, db_conn, data_folder):
        try:
            preparedData = alterProcessAllClassFiles(data_folder)
            insertAlterClassData(db_conn, preparedData)
        except Exception:
            logger.error(f"Error ALTER PARSING class files\n{format_exc()}")
