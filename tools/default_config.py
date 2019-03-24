# default relative paths to data folders; avoids hardcoding

__DefaultPaths = {
    # path to specific file if only one file needs to be handled
    # path to folder if multiple files need to be handled
    "Bestiary" : "tools/files/bestiary/chisaipete_bestiary",
    "Races" : "tools/files/races/Races.xml",
    "Spells" : "tools/files/spells",
    "Feats" : "tools/files/feats/Feats.xml",
    "Classes" : "tools/files/classes",
    "ClassesAlternative" : "tools/files/classes",
}


def getDefaultPaths():
    return __DefaultPaths
