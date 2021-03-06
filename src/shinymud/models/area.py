from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
from shinymud.models.room import Room
from shinymud.models.item import BuildItem
from shinymud.models.npc import Npc
from shinymud.models.script import Script
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.lib.world import World
import time

class Area(Model):
    db_table_name = 'area'
    db_columns = Model.db_columns + [
        Column('name', null=False, unique=True),
        Column('title', default='New Area'),
        Column('builders', read=read_list, 
               write=write_list, copy=copy_list, default=[]),
        Column('level_range', default='All'),
        Column('description', default='No Description'),
        
    ]
    def __init__(self, args={}):
        Model.__init__(self, args)
        self.rooms = {}
        self.items = {}
        self.npcs = {}
        self.scripts = {}
        self.time_of_last_reset = 0
        self.times_visited_since_reset = 0
    
    def load(self):
        """Load all of this area's objects from the database."""
        if self.dbid:
            items = self.world.db.select("* from build_item where area=?", [self.name])
            for item in items:
                item['area'] = self
                self.items[str(item['id'])] = BuildItem(item)
            scripts = self.world.db.select("* from script where area=?", [self.name])
            for script in scripts:
                script['area'] = self
                self.scripts[str(script['id'])] = Script(script)
            npcs = self.world.db.select("* from npc where area=?", [self.name])
            for npc in npcs:
                npc['area'] = self
                self.npcs[str(npc['id'])] = Npc(npc)
            rooms = self.world.db.select("* from room where area=?", [self.name])
            for room in rooms:
                room['area'] = self
                new_room = Room(room)
                new_room.reset()
                self.rooms[str(room['id'])] = new_room
            
            self.time_of_last_reset = time.time()
    
    def __str__(self):
        """Print out a nice string representation of this area's attributes."""
        
        builders = ', '.join(self.builders)
        area_list = ' Area '.center(50, '-')
        area_list +="""
Name: %s (not changeable)
Title: %s
Level Range: %s
Builders: %s
Number of rooms: %s
Number of items: %s
Number of npc's: %s
Number of scripts: %s
Description: \n    %s""" % (self.name, 
                            self.title,
                            self.level_range, 
                            builders.capitalize(),
                            str(len(self.rooms.keys())),
                            str(len(self.items.keys())),
                            str(len(self.npcs.keys())),
                            str(len(self.scripts.keys())),
                            self.description)
        area_list += '\n' + '-'.center(50, '-')
        return area_list
    
    def get_id(self, id_type):
        """Generate a new id for an item, npc, or room associated with this area."""
        if id_type in ['room', 'build_item', 'npc', 'script']:
            rows = self.world.db.select("max(CAST(id AS INT)) as id from " + id_type +" where area=?", [self.name])
            max_id = rows[0]['id']
            if max_id:
                your_id = int(max_id) + 1
            else:
                your_id = 1
            return str(your_id)
    
    def reset(self):
        """Tell all of this area's rooms to reset."""
        for room in self.rooms.values():
            room.reset()
        self.time_of_last_reset = time.time()
    
# ***** BuildMode Accessor Functions *****
    @classmethod
    def create(cls, area_dict={}):
        """Create a new area instance and add it to the world's area list."""
        world = World.get_world()
        name = area_dict.get('name')
        if not name:
            return "Invalid area name. Areas must have a name."
        if world.get_area(name):
            return "This area already exists."
        new_area = cls(area_dict)
        new_area.save()
        world.area_add(new_area)
        return new_area
    
    def build_set_description(self, desc, player=None):
        """Set this area's description."""
        player.last_mode = player.mode
        player.mode = TextEditMode(player, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def build_set_levelrange(self, lvlrange, player=None):
        """Set this area's level range."""
        self.level_range = lvlrange
        self.save()
        return 'Area levelrange set.'
    
    def build_set_title(self, title, player=None):
        """Set this area's title."""
        if not title:
            return 'Type "help areas" for help setting area attributes.'
        self.title = title
        self.save()
        return 'Area title set.'
    
    def build_add_builder(self, playername, player=None):
        """Add a player to the builder's list."""
        self.builders.append(playername)
        self.save()
        return '%s has been added to the builder\'s list for this area.\n' % playername.capitalize()
    
    def build_remove_builder(self, playername, player=None):
        """Remove a player from the builder's list."""
        if playername in self.builders:
            self.builders.remove(playername)
            self.save()
            return '%s has been removed from the builder\'s list for this area.\n' % playername.capitalize()
        else:
            return '%s is not on the builder\'s list for this area.\n' % playername.capitalize()
    
# ************************ Room Functions ************************
# Here exist all the function that an area uses to manage the rooms
# it contains.
    def list_rooms(self):
        room_list = [(' Rooms in area "%s" ' % self.name).center(50, '-')]
        #For now we will sort everything alphabetically by it's name
        stuff = [(each[1].name, each[0]) for each in self.rooms.items()]
        stuff.sort()
        for value, key in stuff:
            room_list.append('%s - %s' % (key, value) )
        room_list.append('-'.center(50, '-') )
        return room_list
    
    def new_room(self, room_dict=None):
        """Add a new room to this area's room list."""
        if room_dict:
            # Create a new room with pre-initialized data
            room_dict['area'] = self
            new_room = Room(room_dict)
        else:
            # Create a new 'blank' room
            new_room = Room.create(self, self.get_id('room'))
        new_room.save()
        self.rooms[str(new_room.id)] = new_room
        return new_room
    
    def get_room(self, room_id):
        """Get a room from this area by its id, if it exists.
        If it does not exist, return None.
        """
        return self.rooms.get(room_id)
    
    def destroy_room(self, room_id):
        """Destroy a specific room in this area."""
        self.world.log.debug('Trying to destroy room %s.' % room_id)
        room = self.get_room(room_id)
        if room:
            if room.players:
                return 'You can\'t destroy that room, there are people in there!.\n'
            doors = room.exits.keys()
            for door in doors:
                room.build_remove_exit(door)
            for spawn in room.spawns.values():
                spawn.destruct()
            room.spawns = {}
            room.id = None
            del self.rooms[room_id]
            room.destruct()
            return 'Room %s has been deleted.\n' % room_id
        return 'Room %s doesn\'t exist.\n' % room_id
    
# ************************ NPC Functions ************************
# Here exist all the function that an area uses to manage the NPC's
# it contains.
    def list_npcs(self):
        """Return a 'pretty list' of all the npcs in this area."""
        npc_list = [(' Npcs in area "%s" ' % self.name).center(50, '-')]
        #For now we will sort everything alphabetically by it's name
        stuff = [(each[1].name, each[0]) for each in self.npcs.items()]
        stuff.sort()
        for value, key in stuff:
            npc_list.append('%s - %s' % (key, value) )
        npc_list.append('-'.center(50, '-') )
        return npc_list
    
    def new_npc(self, npc_dict=None):
        """Add a new npc to this area's npc list."""
        if npc_dict:
            npc_dict['area'] = self
            new_npc = Npc(npc_dict)
        else:
            new_npc = Npc.create(self, self.get_id('npc'))
        new_npc.save()
        self.npcs[str(new_npc.id)] = new_npc
        return new_npc
    
    def get_npc(self, npc_id):
        """Get an npc from this area by its id, if it exists.
        If it does not exist, return None.
        """
        return self.npcs.get(npc_id)
    
    def destroy_npc(self, npc_id):
        npc = self.get_npc(npc_id)
        if not npc:
            return 'That npc doesn\'t exist.'
        npc.destruct()
        for elist in npc.events.values():
            for event in elist:
                event.destruct()
        for ai in npc.ai_packs.values():
            ai.destruct()
        
        npc.ai_packs.clear()
        npc.events.clear()
        npc.id = None
        del self.npcs[npc_id]
        return '"%s" has been successfully destroyed.' % npc.name
    
# ************************ Item Functions ************************
# Here exist all the function that an area uses to manage the items
# it contains.
    def list_items(self):
        item_list = [(' Items in area "%s" ' % self.name).center(50, '-')]
        #For now we will sort everything alphabetically by it's name
        stuff = [(each[1].name, each[0]) for each in self.items.items()]
        stuff.sort()
        for value, key in stuff:
            item_list.append('%s - %s' % (key, value) )
        item_list.append( '-'.center(50, '-') )
        return item_list
    
    def new_item(self, item_dict=None):
        """Add a new item to this area's item list."""
        if item_dict:
            item_dict['area'] = self
            new_item = BuildItem(item_dict)
        else:
            new_item = BuildItem.create(self, self.get_id('build_item'))
        new_item.save()
        self.items[str(new_item.id)] = new_item
        return new_item
    
    def get_item(self, item_id):
        """Get an item from this area by its id, if it exists.
        If it does not exist, return None.
        """
        if item_id in self.items.keys():
            return self.items.get(item_id)
        return None
    
    def destroy_item(self, item_id):
        """Remove this item from this area's items dictionary and from the database
        item_id -- the id of the item
        """
        item = self.get_item(item_id)
        if not item:
            return 'That item doesn\'t exist.\n'
        item.destruct()
        item.id = None
        del self.items[item_id]
        return '"%s" has been successfully destroyed.\n' % item.name
    
# ************************ Script Functions ************************
# Here exist all the function that an area uses to manage the scripts
# it contains.
    def list_scripts(self):
        script_list = [(' Scripts in area "%s" ' % self.name
                      ).center(50, '-')]
        #For now we will sort everything alphabetically by it's name
        stuff = [(each[1].name, each[0]) for each in self.scripts.items()]
        stuff.sort()
        for value, key in stuff:
            script_list.append('%s - %s' % (key, value) )
        script_list.append('-'.center(50, '-') )
        return script_list
    
    def new_script(self, script_dict=None):
        """Add a new script to this area's script list."""
        if script_dict:
            script_dict['area'] = self
            new_script = Script(script_dict)
        else:
            new_script = Script({'area': self, 'id': self.get_id('script')})
        new_script.save()
        self.scripts[str(new_script.id)] = new_script
        return new_script
    
    def get_script(self, script_id):
        """Return the script object associated with script_id (or None
        if the script doesn't exist)
        """
        return self.scripts.get(script_id)
    
    def destroy_script(self, script_id):
        s = self.get_script(script_id)
        if not s:
            return 'That script doesn\'t exist.'
        s.destruct()
        s.id = None
        del self.scripts[script_id]
        return 'Script "%s" has been successfully destroyed.' % script_id
    

model_list.register(Area)
