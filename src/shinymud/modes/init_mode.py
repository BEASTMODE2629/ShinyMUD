from shinymud.commands import *
from shinymud.world import World

class InitMode(object):
    
    def __init__(self, user):
        self.user = user
        self.user.update_output("Enter username: ")
        self.state = self.verify_username
        self.active = True
        self.name = 'InitMode'
    
    def verify_username(self):
        if len(self.user.inq) > 0:
            username = self.user.inq[0]
            if username:
                self.username = username.replace('\n', '')
                self.state = self.verify_password
                del self.user.inq[0]
                self.user.update_output("Enter password: ")
    
    def verify_password(self):
        if len(self.user.inq) > 0:
            password = self.user.inq.pop(0)
            if password:
                self.user.name = self.username
                self.character_cleanup()
            else:
                self.state = self.verify_username
                self.user.update_output("Bad username or password.\n Enter username: ")
    
    def join_world(self):
        self.active = False
        WorldEcho(self.user, "%s has entered the world." % self.user.get_fancy_name()).execute()
    
    def character_cleanup(self):
        world = World.get_world()
        world.user_add(self.user)
        world.user_remove(self.user.conn)
        self.state = self.join_world
    
