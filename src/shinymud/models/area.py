from shinymud.lib.world import World
from shinymud.models.room import Room
from shinymud.models.item import Item
from shinymud.models.npc import Npc
from shinymud.models.script import Script
from shinymud.modes.text_edit_mode import TextEditMode
import time

class Area(object):
    
    def __init__(self, name=None, **args):
        self.name = str(name)
        self.title = args.get('title', 'New Area')
        self.rooms = {}
        self.items = {}
        self.npcs = {}
        self.scripts = {}
        builders = args.get('builders')
        if builders:
            self.builders = builders.split(',')
        else:
            self.builders = []
        self.level_range = args.get('level_range', 'All')
        self.description = args.get('description', 'No Description')
        self.dbid = args.get('dbid')
        self.world = World.get_world()
        self.time_of_last_reset = 0
        self.times_visited_since_reset = 0
    
    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['level_range'] = self.level_range
        d['builders'] = ",".join(self.builders)
        d['description']  = self.description
        d['title'] = self.title
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def load(self):
        if self.dbid:
            items = self.world.db.select("* from item where area=?", [self.dbid])
            for item in items:
                item['area'] = self
                self.items[str(item['id'])] = Item(**item)
            scripts = self.world.db.select("* from script where area=?", [self.dbid])
            for script in scripts:
                script['area'] = self
                self.scripts[str(script['id'])] = Script(**script)
            npcs = self.world.db.select("* from npc where area=?", [self.dbid])
            for npc in npcs:
                npc['area'] = self
                self.npcs[str(npc['id'])] = Npc(**npc)
            rooms = self.world.db.select("* from room where area=?", [self.dbid])
            for room in rooms:
                room['area'] = self
                new_room = Room(**room)
                new_room.reset()
                self.rooms[str(room['id'])] = new_room
            
            self.time_of_last_reset = time.time()
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('area', save_dict)
            else:    
                self.world.db.update_from_dict('area', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('area', self.to_dict())
    
    def destruct(self):
        if self.dbid:
            self.world.db.delete('FROM area WHERE dbid=?', [self.dbid])
    
    def add_builder(self, username):
        """Add a user to the builder's list."""
        self.builders.append(username)
        self.save()
        return '%s has been added to the builder\'s list for this area.\n' % username.capitalize()
    
    def remove_builder(self, username):
        """Remove a user from the builder's list."""
        if username in self.builders:
            self.builders.remove(username)
            self.save()
            return '%s has been removed from the builder\'s list for this area.\n' % username.capitalize()
        else:
            return '%s is not on the builder\'s list for this area.\n' % username.capitalize()
    
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
    
    def list_rooms(self):
        names = self.rooms.keys()
        room_list = (' Rooms in area "%s" ' % self.name).center(50, '-') + '\n'
        for key, value in self.rooms.items():
            room_list += '%s - %s\n' % (key, value.name)
        room_list += '-'.center(50, '-')
        return room_list
    
    def list_items(self):
        names = self.items.keys()
        item_list = (' Items in area "%s" ' % self.name).center(50, '-') + '\n'
        for key, value in self.items.items():
            item_list += '%s - %s\n' % (key, value.name)
        item_list += '-'.center(50, '-')
        return item_list
    
    def list_npcs(self):
        names = self.npcs.keys()
        npc_list = (' Npcs in area "%s" ' % self.name).center(50, '-') + '\n'
        for key, value in self.npcs.items():
            npc_list += '%s - %s\n' % (key, value.name)
        npc_list += '-'.center(50, '-')
        return npc_list
    
    def list_scripts(self):
        names = self.npcs.keys()
        script_list = (' Scripts in area "%s" ' % self.name
                      ).center(50, '-') + '\n'
        for key, value in self.scripts.items():
            script_list += '%s - %s\n' % (key, value.name)
        script_list += '-'.center(50, '-')
        return script_list
    
    @classmethod
    def create(cls, name, **area_dict):
        """Create a new area instance and add it to the world's area list."""
        world = World.get_world()
        if world.get_area(name):
            return "This area already exists.\n"
        if area_dict:
            new_area = cls(name, **area_dict)
        else:
            new_area = cls(name)
        new_area.save()
        world.new_area(new_area)
        return new_area
    
    def get_id(self, id_type):
        """Generate a new id for an item, npc, or room associated with this area."""
        if id_type in ['room', 'item', 'npc', 'script']:
            world = World.get_world()
            rows = world.db.select("max(id) as id from " + id_type +" where area=?", [self.dbid])
            max_id = rows[0]['id']
            if max_id:
                your_id = int(max_id) + 1
            else:
                your_id = 1
            return str(your_id)
    
    def set_description(self, desc, user=None):
        """Set this area's description."""
        user.last_mode = user.mode
        user.mode = TextEditMode(user, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.\n'
    
    def set_levelrange(self, lvlrange, user=None):
        """Set this area's level range."""
        self.level_range = lvlrange
        self.save({'level_range': self.level_range})
        return 'Area levelrange set.'
    
    def set_title(self, title, user=None):
        """Set this area's title."""
        if not title:
            return 'Type "help areas" for help setting area attributes.'
        self.title = title
        self.save({'title': self.title})
        return 'Area title set.'
    
    def reset(self):
        """Tell all of this area's rooms to reset."""
        for room in self.rooms.values():
            room.reset()
        self.time_of_last_reset = time.time()
    
# ************************ Room Functions ************************
# Here exist all the function that an area uses to manage the rooms
# it contains.
    def destroy_room(self, room_id):
        """Destroy a specific room in this area."""
        room = self.get_room(room_id)
        if room:
            if room.users:
                return 'You can\'t destroy that room, there are people in there!.\n'
            doors = room.exits.keys()
            for door in doors:
                room.remove_exit(door)
            for reset in room.resets:
                reset.destruct()
            room.resets = {}
            room.id = None
            del self.rooms[room_id]
            room.destruct()
            return 'Room %s has been deleted.\n' % room_id
        return 'Room %s doesn\'t exist.\n' % room_id
    
    def new_room(self, room_dict=None):
        """Add a new room to this area's room list."""
        if room_dict:
            # Create a new room with pre-initialized data
            new_room = Room(**room_dict)
        else:
            # Create a new 'blank' room
            new_room = Room.create(self, self.get_id('room'))
        new_room.save()
        self.rooms[str(new_room.id)] = new_room
        return new_room
    
    def new_item(self, item_dict=None):
        """Add a new item to this area's item list."""
        if item_dict:
            new_item = Item(**item_dict)
        else:
            new_item = Item.create(self, self.get_id('item'))
        new_item.save()
        self.items[str(new_item.id)] = new_item
        return new_item
    
    def new_npc(self, npc_dict=None):
        """Add a new npc to this area's npc list."""
        if npc_dict:
            new_npc = Npc(**npc_dict)
        else:
            new_npc = Npc.create(self, self.get_id('npc'))
        new_npc.save()
        self.npcs[str(new_npc.id)] = new_npc
        return new_npc
    
    def new_script(self, script_dict=None):
        """Add a new script to this area's script list."""
        if script_dict:
            new_script = Script(**script_dict)
        else:
            new_script = Script(self, self.get_id('script'))
        new_script.save()
        self.scripts[str(new_script.id)] = new_script
        return new_script
    
    def get_item(self, item_id):
        """Get an item from this area by its id, if it exists.
        If it does not exist, return None."""
        if item_id in self.items.keys():
            return self.items.get(item_id)
        return None
        
    def get_room(self, room_id):
        """Get a room from this area by its id, if it exists.
        If it does not exist, return None."""
        return self.rooms.get(room_id)
    
    def get_npc(self, npc_id):
        """Get an npc from this area by its id, if it exists.
        If it does not exist, return None."""
        return self.npcs.get(npc_id)
    
    def get_script(self, script_id):
        return self.scripts.get(script_id)
    
# ************************ NPC Functions ************************
# Here exist all the function that an area uses to manage the NPC's
# it contains.
    def destroy_npc(self, npc_id):
        npc = self.get_npc(npc_id)
        if not npc:
            return 'That npc doesn\'t exist.\n'
        npc.destruct()
        npc.id = None
        del self.npcs[npc_id]
        return '"%s" has been successfully destroyed.\n' % npc.name
    
# ************************ Item Functions ************************
# Here exist all the function that an area uses to manage the items
# it contains.
    def destroy_item(self, item_id):
        item = self.get_item(item_id)
        if not item:
            return 'That item doesn\'t exist.\n'
        item.destruct()
        item.id = None
        del self.items[item_id]
        return '"%s" has been successfully destroyed.\n' % item.name
    
