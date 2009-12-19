I don't know the format of this file yet, but I do know that it will describe all of the tables in the
database. It will probably be in sql, or python, depending on which is easier to build.





CREATE TABLE user (
    dbid INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    channels TEXT,
    password TEXT NOT NULL,
    strength INTEGER NOT NULL DEFAULT 0,
    intelligence INTEGER NOT NULL DEFAULT 0,
    dexterity INTEGER NOT NULL DEFAULT 0
);



CREATE TABLE area (
    dbid INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    level_range TEXT,
    builders TEXT,
    description TEXT
);




CREATE TABLE room (
    dbid INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    area INTEGER NOT NULL REFERENCES area(dbid),
    title TEXT,
    description TEXT,
    UNIQUE (area, id)
);



CREATE TABLE  item (
    dbid INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    area INTEGER NOT NULL REFERENCES area(dbid),
    name TEXT,
    title TEXT,
    description TEXT,
    keywords TEXT,
    weight INTEGER DEFAULT 0,
    base_value INTEGER DEFAULT 0,
    pickup TEXT,
    equip_slot INTEGER,
    is_container TEXT,
    UNIQUE (area, id)
);



CREATE TABLE room_exit (
    dbid INTEGER PRIMARY KEY,
    room INTEGER NOT NULL REFERENCES room(dbid),
    to_room INTEGER NOT NULL REFERENCES room(dbid),
    linked_exit INTEGER REFERENCES room_exit(dbid),
    direction TEXT NOT NULL,
    openable TEXT,
    closed TEXT,
    hidden TEXT,
    locked TEXT,
    key INTEGER REFERENCES item(dbid),
    UNIQUE (room, direction)
);





CREATE TABLE inventory (
    dbid INTEGER PRIMARY KEY,
    template INTEGER NOT NULL REFERENCES item(dbid),
    name TEXT,
    title TEXT,
    description TEXT,
    keywords TEXT,
    weight INTEGER DEFAULT 0,
    base_value INTEGER DEFAULT 0,
    pickup TEXT,
    equip_slot INTEGER,
    is_container TEXT,
    owner INTEGER REFERENCES user(dbid),
    container INTEGER REFERENCES inventory(dbid)
);

CREATE TABLE npc (
    dbid INTEGER PRIMARY KEY

);


CREATE TABLE room_npc_resets (
    room INTEGER NOT NULL REFERENCES room(dbid),
    npc INTEGER NOT NULL REFERENCES npc(dbid),
    PRIMARY KEY (room, npc)
);


CREATE TABLE room_item_resets (
    room INTEGER NOT NULL REFERENCES room(dbid),
    item INTEGER NOT NULL REFERENCES item(dbid),
    PRIMARY KEY (room, item)
);