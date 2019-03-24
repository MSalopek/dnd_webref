import json
import sqlite3
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def _db_query(query, args=(), one=False):
    with get_db() as cur:               # this should auto commit/rollback
        res = cur.execute(query, args)
        rv = res.fetchall()
        return (rv[0] if rv else None) if one else rv


def get_subclasses_names():
    rows = _db_query("""SELECT DISTINCT cls_name, url_name, subcls_name 
                    FROM classes""")
    subclasses_names = {}
    for row in rows:
        if row['cls_name'] in subclasses_names:
            subclasses_names[row['cls_name']].append((row['subcls_name'], row['url_name']))
        else:
            subclasses_names[row['cls_name']] = [(row['subcls_name'], row['url_name'])]
    return subclasses_names


def get_races_names():
    rows = _db_query("""SELECT DISTINCT url_name, name 
                FROM races""")
    return {i['name']: i['url_name'] for i in rows}


def get_subclass_data(subcls_url_name):
    # NOTE this is a quick and DIRTY HACK
    # I don't have time to fiddle with files...
    rws = _db_query("""SELECT features 
                            FROM classes
                                WHERE url_name = ?""", (subcls_url_name, ))
    dct = [json.loads(i['features']) for i in rws]
    keys = []
    for i in dct:
        for key in i.keys():
            keys.append(key)
    key_set = set(keys)
    common = [key for key in key_set if key[0].islower()]
    
    # this is here because I don't have time to fix class XMLs
    # this removes extra unwanted keys from keys shared by subclasses
    keys_to_remove = ["savingThrows", "spellAbility", "name", "hd"]
    keys_to_remove = ["savingThrows", "spellAbility", "name", "hd"]
    for key in keys_to_remove:
        try:
            common.remove(key)
        except:
            pass

    full_features = {k:v for k,v in dct[-1].items() if k not in common}
    agg = {k:[] for k in common}
    # aggregate features
    for k in agg.keys():
        for i in dct:
            agg[k].append(i[k])
    if "slots" in agg.keys():
        old = agg['slots']
        agg['slots'] = [i.split(",") for i in old]
    ready_data = {
        "table_data":agg,
        "features": full_features
    }
    return ready_data


def get_bestiary() -> dict:
    result = _db_query("SELECT name, ac, hp, size, cr, aligned from bestiary")
    return [
        {
            "name": i["name"],
            "ac": i["ac"],
            "hp": i["hp"],
            "size": i["size"],
            "cr": i["cr"],
            "aligned": i["aligned"]
       }
        for i in result
    ]


def get_beast_info(beast_name) -> dict:
    # HACK bcs database is poorly thought out
    details_list = ["Damage Immunities", "Damage Vulnerabilities", 
    "Damage Resistances", "Senses", "Languages", "Traits"]
    result = _db_query("""SELECT full_desc_json
                            FROM bestiary
                                WHERE name = ?""", (beast_name,), one=True)
    old = json.loads(result["full_desc_json"])
    details = {}
    for key in details_list:
        if old.get(key, False):
            details[key] = old.pop(key)
    prepared = {k: v for k,v in old.items()}
    prepared.update({"details": details})
    return prepared

def get_feats():
    feats = _db_query("""SELECT name, description 
                                FROM feats""")
    return [{"name": i["name"], "text": i["description"]} for i in feats]


def get_spells() -> Dict[int, List]:
    keys = ["name", 
            "url_name", 
            "level",
            "classes",
            "school", 
            "time",
            "components", 
            "concentration", 
            "duration",
            "ritual" ]
    spells = _db_query("""SELECT name, url_name, 
                                level, school, 
                                time, components, 
                                concentration, classes, 
                                duration, ritual 
                                FROM spells""")
    prepared_spells = defaultdict(list)
    for i in spells:
        spell_dict = {}
        for key in keys:
            spell_dict[key] = i[key]
        prepared_spells[spell_dict["level"]].append((spell_dict))
    return dict(prepared_spells)


def get_spells_for_class(class_name):
    all_spells = get_spells() # dict[int, list]
    class_spells = defaultdict(list)
    for k,v in all_spells.items():
        class_spells[k] = list(filter(lambda x: class_name in x["classes"], v))
    return dict(class_spells)


def get_single_spell(url_name):
    translate_school = {
        "EV": "Evocation",
        "C": "Conjuration",
        "N": "Necromancy",
        "A": "Abjuration",
        "D": "Divintation",
        "T": "Transmutation",
        "EN": "Enchantment",
        "I": "Illusion",

    }
    keys = [
        "name", 
        "level",
        "classes",
        "school", 
        "time",
        "components", 
        "concentration", 
        "duration",
        "ritual",
        "_text",
        "_range" ]
    spell = _db_query("SELECT * FROM spells WHERE url_name = ?", (url_name,), one=True)
    spell_dict =  {key:spell[key] for key in keys}
    spell_dict["school"] = translate_school[spell_dict["school"]]
    return spell_dict


def get_alter_class(cls_name):
    row = _db_query("""SELECT cls_name, col_names, 
                        prog_table, base_features, subclasses
                        FROM classes_alter
                            WHERE url_name = ?""", (cls_name,), one=True)
    modified_base = json.loads(row["base_features"])
    try:
        # all share this data
        hd = modified_base.pop("hd")
        saving_throws = modified_base.pop("savingThrows")
        modified_base["Starting Proficiencies"] = f"Hit Die: d{hd}\nSaving Throws: {saving_throws}\n" + modified_base["Starting Proficiencies"]
                
        # spellcasters only
        del modified_base["name"]
        del modified_base["spellAbility"]
    except:
        pass

    return {
        "name": row["cls_name"].title(),
        "col_names": json.loads(row["col_names"]),
        "prog_table":json.loads( row["prog_table"]),
        "base_features": modified_base,
        "subclasses": json.loads(row["subclasses"])
    }


def get_subrace(subrace_url_name):
    row = _db_query("""SELECT subrace_name, features
                        FROM races
                            WHERE subrace_url_name = ?""", (subrace_url_name,), one=True)
    return {
        "name": row["subrace_name"],
        "features": json.loads(row["features"])
    }
