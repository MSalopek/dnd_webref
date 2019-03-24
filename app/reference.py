from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from .db import (
    get_subclasses_names, 
    get_races_names, get_subclass_data,
    get_bestiary, get_beast_info, get_feats, get_spells,
    get_spells_for_class, get_single_spell,
    get_alter_class, get_subrace
)

from .mcks import col_names
from .mcks import data as d2fd

bp = Blueprint("reference", __name__, url_prefix="/reference", template_folder="templates")


@bp.route("/", methods=["GET"])
def index_pg():
    return render_template("index.html")

@bp.route("/bestiary", methods=["GET"])
def bestiary_pg():
    beasts_list = sorted(get_bestiary(), key=lambda x: x['name'])
    return render_template("bestiary.html", data=beasts_list)


@bp.route("/bestiary/<beast_name>", methods=["GET"])
def beast_pg(beast_name):
    beast = get_beast_info(beast_name)
    return render_template("beast.html", data=beast)


@bp.route("/feats", methods=["GET"])
def feats_pg():
    feats = get_feats()
    return render_template("feats.html", data=feats)


@bp.route("/spells/all", methods=["GET"])
def spells_pg():
    spells = get_spells()
    return render_template("spells.html", data=spells)


@bp.route("/spells/class/<caster_class>", methods=["GET"])
def spells_by_class(caster_class):
    spells = get_spells_for_class(caster_class)
    return render_template("spells.html", data=spells, name=caster_class)


@bp.route("/spells/view/<spell_url>", methods=["GET"])
def spells_view_single(spell_url):
    spell = get_single_spell(spell_url)
    return render_template("view_spell.html", data=spell)


@bp.route("/classes/<cls_url_name>", methods=["GET"])
def classes_view_single(cls_url_name):
    data = get_alter_class(cls_url_name)
    return render_template("full_class.html",
            cls_name=data["name"],
            col_names=data["col_names"],
            base=data["base_features"],
            prog_table=data["prog_table"],
            subclasses=data["subclasses"]
        )


@bp.route("/races/<subrace_url_name>", methods=["GET"])
def races_view_single(subrace_url_name):
    data = get_subrace(subrace_url_name)
    return render_template("race.html", data=data)
