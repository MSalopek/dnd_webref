CREATE TABLE IF NOT EXISTS bestiary (
    name NOT NULL UNIQUE,
    ac INT,
    hp INT,
    size TEXT, 
    cr TEXT, 
    aligned TEXT, 
    full_desc_json TEXT DEFAULT "{}"
);

CREATE TABLE IF NOT EXISTS spells (
    url_name TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    level INTEGER,
    school TEXT,
    time TEXT,
    _range TEXT,
    components TEXT,
    duration TEXT,
    concentration TEXT,
    ritual TEXT,
    classes TEXT,
    _text TEXT
);

CREATE TABLE IF NOT EXISTS classes (
    url_name TEXT NOT NULL,
    cls_name TEXT NOT NULL,
    subcls_name TEXT NOT NULL,
    level INTEGER,
    features TEXT
);

CREATE TABLE IF NOT EXISTS classes_alter (
    url_name TEXT NOT NULL,
    cls_name TEXT NOT NULL,
    col_names TEXT,
    prog_table TEXT,
    base_features TEXT,
    subclasses TEXT
);

CREATE TABLE IF NOT EXISTS races (
    subrace_url_name TEXT NOT NULL,
    subrace_name TEXT NOT NULL,
    race_name TEXT NOT NULL,
    features TEXT
);

CREATE TABLE IF NOT EXISTS feats (
    url_name NOT NULL,
    name TEXT NOT NULL,
    description TEXT
);
