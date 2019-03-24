# classes alter parsing
from collections import defaultdict, OrderedDict
import xml.etree.ElementTree as etree
from traceback import format_exc
import json

class OrderedDefaultDict(OrderedDict):
    factory = dict

    def __missing__(self, key):
        self[key] = value = self.factory()
        return value

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


def alterProcessClassXML(file_path):
    tree = etree.parse(file_path)
    root = tree.getroot()
    # table_data = defaultdict(dict)
    # base_features_data = defaultdict(dict)
    # subclass_data = defaultdict(dict)
    table_data = OrderedDefaultDict()
    base_features_data = OrderedDefaultDict()
    subclass_data = OrderedDefaultDict()
    for _class in root:
        for elem in _class:
            table_data_dict = {}
            if elem.attrib.get("level", False):
                if elem.attrib["level"] == "0":
                    # NOTE DONE
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


if __name__ == "__main__":
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)
    path_str = "/home/ms/projects/dnd_webref/tools/files/classes/revised_bard_new.xml"
    names = alterProcessClassXML(path_str)
    pp.pprint(names)
