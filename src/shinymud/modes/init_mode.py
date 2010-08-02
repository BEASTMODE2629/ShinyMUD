from shinymud.commands.commands import *
from shinymud.data.config import GAME_NAME
from shinymud.lib.ansi_codes import CONCEAL, CLEAR, COLOR_FG_RED
from shinymud.lib.world import World

import hashlib
import re

BAD_PASSWORDS = ['cancel', '@cancel', 'password', 'passwd']

# choose_class_string = """Choose a class, or pick custom:
# Fighter    Thief      Wizard     Custom
# STR:  3    STR:  1    STR:  1    STR: ?
# DEX:  1    DEX:  3    DEX:  1    DEX: ?
# INT:  0    INT:  1    INT:  3    INT: ?
# SPD:  1    SPD:  3    SPD:  0    SPD: ?
#  HP: 35     HP: 20     HP: 20     HP: ?
#  MP:  0     MP:  0     MP:  6     MP: ?
# """

class InitMode(object):
    """InitMode is a giant state machine that handles the self.world.log-in and character
    create process.
    Each function in the InitMode class is meant to be (more or less) a single
    state in the self.world.log-in or character creation process. Each state-function
    takes care of designating which state-function gets executed next by
    setting the self.state or self.next_state functions (depending on whether
    the next state-function requires player input or not).
    -
    The difference between self.state and self.next_state:
    self.state is what gets executed by the World every turn. It cannot be
    None, or the player will no longer recieve their turn from the world.
    -
    self.next_state gets executed by self.get_input, so that self.get_input
    can guard for player input, clean it, and deliver it to whichever state
    function is stored in self.next_state.
    -
    If your state function needs player input, then self.state should point to
    self.get_input (to guard for player input each turn of the world) and 
    self.next_state should point to your state_function.
    """
    def __init__(self, player):
        """
        player - a Player object that has yet to be playerized (player-initialized)
        """
        self.player = player
        self.newbie = False
        self.state = self.intro
        self.active = True
        self.name = 'InitMode'
        self.world = World.get_world()
        self.save = {}
    
    def get_input(self):
        """Get input from the player and pass it to the appropriate function.
        
        This function waits until there is player input (we are not guaranteed to
        get player-input on each world turn), then cleans up any newlines or
        whitespace and sends it to the next state-function stored in
        self.next_state.
        """
        if len(self.player.inq) > 0:
            # We've got something to work with!
            arg = self.player.inq[0].strip().replace('\r', '').replace('\n', '')
            del self.player.inq[0]
            self.next_state(arg)
    
    def intro(self):
        """Output the intro Message.
        
        PREV STATE: None (this should be the first state function in InitMode)
        NEXT STATE: self.verify_playername
        """
        if self.player.win_size[0] < 80:
            self.player.update_output("Welcome to %s!\r\n" % GAME_NAME, strip_nl=False)
        else:
            self.player.update_output(self.world.login_greeting + '\r\n', strip_nl=False)
        
        intro_message = 'Type "new" if you\'re a new player. Otherwise, enter your name.'
        self.player.update_output(intro_message)
        self.state = self.get_input
        self.next_state = self.verify_playername
    
    def verify_playername(self, arg):
        """Get the name of the player self.world.logging in. If the player exists, grab their
        data and verify their password. Otherwise, start the character creation
        process.
        
        PREV STATE: self.intro
        NEXT STATE: self.verify_password, if the player self.world.logging in exists, OR
                    self.verify_new_character if the player self.world.logging in is new
        """
        playername = arg
        if playername:
            if playername.lower() == 'new':
                self.next_state = self.new_playername
                self.player.update_output('Please choose a name. It should be a single word, using only letters.')
            else:
                self.playername = playername
                row = self.world.db.select('password,dbid FROM player WHERE name=?', [self.playername])
                if row:
                    # Awesome, a player with this name does exist! Let's check their password!
                    self.password = row[0]['password']
                    self.dbid = row[0]['dbid']
                    # self.state = self.verify_password
                    self.player.update_output("Enter password: " + CONCEAL, False)
                    self.next_state = self.verify_password
                else:
                    # The player entered a name that doesn't exist.. they should create
                    # a new character or try entering the name again.
                    self.player.update_output('That player doesn\'t exist. Would you like to create a new character by the name of %s? (Yes/No)' % self.playername)
                    self.next_state = self.verify_new_character
    
    def verify_password(self, arg):
        """Verify that the password provided by the player and the password from
        their database profile are correct.
        
        PREV STATE: self.verify_playername
        NEXT STATE: self.character_cleanup, if the correct password was provided
                    self.verify_playername, if an incorrect password was provided
        """
        password = hashlib.sha1(arg).hexdigest()
        if password == self.password:
            # Wicked cool, our player exists AND the right person is self.world.logging in
            self.player.playerize(self.world.db.select('* FROM player WHERE dbid=?', [self.dbid])[0])
            # Make sure that we clear the concealed text effect that we 
            # initiated when we moved to the password state
            self.player.update_output(CLEAR, False)
            self.state = self.character_cleanup
        else:
            self.next_state = self.verify_playername
            self.player.update_output(CLEAR + "\r\nBad playername or password. Enter playername:")
    
    def join_world(self):
        """The final stop in our InitMode state machine! 
        We set the state of InitMode to inactive and tell the player they have 
        entered the world!
        """
        self.active = False
        self.player.update_output('\nYou have entered the world of %s.\n' % GAME_NAME, strip_nl=False)
        if self.newbie:
            nl = '*' + (' ' * 67) + '*\n'
            newb = ' Welcome, new player! '.center(69, '*') + '\n' + nl
            newb += ('* If you would like some help playing the game, type "help newbie". *').center(69, ' ') + '\n' + nl
            newb += ('*' * 69)
            self.player.update_output(newb, strip_nl=False)
            self.world.tell_players("%s, a new player, has entered the world." % self.player.fancy_name())
            self.world.play_log.info('New player "%s" created.' % self.player.name)
        else:
            self.world.tell_players("%s has entered the world." % self.player.fancy_name())
        if self.player.location:
            self.player.update_output(self.player.look_at_room())
            self.player.location.add_char(self.player)
        self.world.play_log.info('Player "%s" logging in from: %s.' % (self.player.fancy_name(), str(self.player.addr)))
    
    def character_cleanup(self):
        """This is the final stage before the player enters the world, where any
        cleanup should happen so that the player can be handed off to the main
        parse-command mode.
        
        PREV STATE: self.verify_password OR self.add_email
        NEXT STATE: self.join_world
        """
        # If the player doesn't have a location, send them to the default 
        # location that the World tried to get out of the config file
        if not self.player.location:
            self.player.location = self.world.default_location
        self.player.inq = []
        self.world.player_add(self.player)
        self.world.player_remove(self.player.conn)
        self.state = self.join_world
    
    # ************Character creation below!! *************
    def verify_new_character(self, arg):
        """A player entered a playername that doesn't exist; ask if they want to
        create a new player by that name.
        
        PREV STATE: self.verify_playername
        NEXT STATE: self.create_password, if the player wants to create a new character, OR
                    self.verify_playername, if the player does not want to create a new character OR
                    self.new_playername if the player entered an invalid playername the first time
        """
        if arg.strip().lower().startswith('y'):
            if self.playername.isalpha():
                self.save['name'] = self.playername.lower()
                self.player.update_output('Please choose a password: ' + CONCEAL, False)
                self.password = None
                self.next_state = self.create_password
            else:
                self.player.update_output("Invalid name. Names should be a single word, using only letters.\r\n" +\
                "Choose a name: ", False)
                self.next_state = self.new_playername
        else:
            self.player.update_output('Type "new" if you\'re a new player. Otherwise, enter your playername.')
            self.next_state = self.verify_playername
    
    def new_playername(self, arg):
        """The player is choosing a name for their new character.
        
        PREV STATE: self.verify_playername
        NEXT STATE: self.create_password
        """
        if arg.isalpha():
            row = self.world.db.select("dbid from player where name=?", [arg.lower()])
            if row:
                self.player.update_output('That playername is already taken.\r\n')
                self.player.update_output('Please choose a playername. It should be a single word, using only letters.')
            else:
                #verify here!
                self.save['name'] = arg.lower()
                self.player.update_output('Please choose a password: ' + CONCEAL, False)
                self.password = None
                self.next_state = self.create_password
        else:
            self.player.update_output("Invalid name. Names should be a single word, using only letters.\r\n" +\
            "Choose a name: ", False)
    
    def create_password(self, arg):
        """The player is choosing a password for their new character.
        
        PREV STATE: self.new_playername OR self.verify_new_character
        NEXT STATE: This state will repeat until a password has been chosen and
                    confirmed, then will change to self.choose_gender
        """
        if not self.password:
            if arg in BAD_PASSWORDS:
                self.player.update_output(CLEAR + '\r\nThat\'s a reserved word. Pick a different password: ' + CONCEAL, False)
            else:    
                self.password = hashlib.sha1(arg).hexdigest()
                self.player.update_output(CLEAR + '\r\nRe-enter your password to confirm: ' + CONCEAL, False)
        else:
            if self.password == hashlib.sha1(arg).hexdigest():
                self.save['password'] = self.password
                self.next_state = self.choose_gender
                self.player.update_output(CLEAR + "\r\nWhat gender shall your character be? Choose from: neutral, female, or male.")
            else:
                self.player.update_output(CLEAR + '\r\nPasswords did not match.' +\
                                        '\r\nPlease choose a password: ' + CONCEAL, False)
                self.password = None
            
    
    def choose_gender(self, arg):
        """The player is choosing a gender for their new character.
        
        PREV STATE: self.create_password
        NEXT STATE: This state will repeat until a gender is chosen, then change
                    to self.add_email
        """
        if arg[0].lower() in 'mfn':
            genders = {'m': 'male', 'f': 'female', 'n': 'neutral'}
            self.save['gender'] = genders.get(arg[0])
            self.player.update_output('If you add an e-mail to this account, we can help you reset ' +\
                                    'your password if you forget it (otherwise, you\'re out of luck ' +\
                                    'if you forget!).\n' +\
                                    'Would you like to add an e-mail address to this character? ' +\
                                    '(Y/N)')
            self.next_state = self.add_email
        else:
            self.player.update_output('Please choose from male, female, or neutral:')
    
    def add_email(self, arg):
        """The player is adding (or not adding!) an email address to their new
        character.
        
        PREV STATE: self.choose_gender
        NEXT_STATE: self.character_cleanup
        """
        if arg.lower().startswith('y'):
            self.save['email'] = 'yes_email'
            self.player.update_output('We promise not to use your e-mail for evil!\n' +\
                                    'Please enter your e-mail address:')
        # We should only get to this state if the player said they want to enter their e-mail
        # address to be saved
        elif self.save.get('email') == 'yes_email':
            self.save['email'] = arg
            self.player.playerize(self.save)
            self.player.save()
            self.state = self.character_cleanup
            self.newbie = True
        else:
            self.player.playerize(self.save)
            self.player.save()
            self.state = self.character_cleanup
            self.newbie = True
    
    # def assign_defaults(self):
    #     if len(self.player.inq) > 0:
    #         if len(self.player.inq[0]) > 0 and self.player.inq[0][0].lower() in 'ctfw':
    #             self.player.playerize(self.save)
    #             if self.player.inq[0][0].lower() == 'c':
    #                 # Custom stats creation
    #                 self.state = self.custom_create
    #                 self.custom_points = {'left':8, 'STR':0, 'INT':0, 'DEX':0, 'SPD':0, 'HP':0, 'MP':0}
    #                 self.display_custom_create()
    #                 del self.player.inq[0]
    #                 return
    #             elif self.player.inq[0][0].lower() == 't':
    #                 # Set Thief defaults
    #                 self.player.strength = 1
    #                 self.player.dexterity = 3
    #                 self.player.intelligence = 1
    #                 self.player.speed = 3
    #                 self.player.max_hp = 20
    #                 self.player.max_mp = 0
    #                 self.player.hp = self.player.max_hp
    #                 self.player.mp = self.player.max_mp
    #             elif self.player.inq[0][0].lower() == 'f':
    #                 # Set Fighter defaults
    #                 self.player.strength = 3
    #                 self.player.dexterity = 1                
    #                 self.player.intelligence = 0
    #                 self.player.speed = 1
    #                 self.player.max_hp = 35
    #                 self.player.max_mp = 0
    #                 self.player.hp = self.player.max_hp
    #                 self.player.mp = self.player.max_mp
    #             elif self.player.inq[0][0].lower() == 'w':
    #                 # Set wizard defaults
    #                 self.player.strength = 1
    #                 self.player.dexterity = 1                
    #                 self.player.intelligence = 3
    #                 self.player.speed = 0
    #                 self.player.max_hp = 20
    #                 self.player.max_mp = 9
    #                 self.player.hp = self.player.max_hp
    #                 self.player.mp = self.player.max_mp
    #             self.state = self.character_cleanup
    #             self.player.dbid = self.world.db.insert_from_dict('player', self.player.to_dict())
    #         else:
    #             # player's input didn't make any sense
    #             del self.player.inq[0]
    #             self.player.update_output("I don't understand." + choose_class_string)
    # 
    # def display_custom_create(self):
    #     header = []
    #     header.append("You have %s points to spend:" % self.custom_points['left'])
    #     header.append("Ability:    Cost:    Effect:")
    #     for ability in ['STR', 'DEX', 'INT', 'SPD', 'HP', 'MP']:
    #         if ability == 'HP':
    #             base = 20
    #             delta = 5
    #         elif ability == 'MP':
    #             base = 0
    #             delta = 3
    #         else:
    #             base = 0
    #             delta = 1
    #         a = self.custom_points[ability]
    #         if a < 3:
    #             values = (ability," " * (14-len(ability)), '1', str(base + (a * delta)), str(base + ((a + 1) * delta)))
    #         else:
    #             values = (ability," " * (14-len(ability)), '*', str(base + (a * delta)), str(base + (a * delta)))
    #         header.append("%s%s%s      %s -> %s" % values)
    #     header.append('Choose an ability and how many points to add (up to three)')
    #     header.append('or negative numbers to remove points. Type "Done" when finished.')
    #     header.append("") # one more newline for easier to read input
    #     self.player.update_output('\n'.join(header))
    # 
    # def custom_create(self):
    #     if len(self.player.inq) > 0:
    #         m = re.match('(?P<attr>[a-zA-Z]+)[ ]*(?P<amount>-?\d+)?', self.player.inq[0])
    #         if m:
    #             attr, amount = m.group('attr', 'amount')
    #             if amount:
    #                 amount = int(amount)
    #             attr = attr.upper()
    #             if attr in self.custom_points:
    #                 new_val = self.custom_points[attr] + amount
    #                 new_balance = self.custom_points['left'] - amount
    #                 if new_val < 0 or new_val > 3 or new_balance < 0 or new_balance > 8:
    #                     self.player.update_output("You can't do that!\n")
    #                 else:
    #                     self.custom_points[attr] = new_val
    #                     self.custom_points['left'] = new_balance
    #             elif attr == 'DONE':
    #                 if self.custom_points['left'] > 0:
    #                     self.player.update_output('You still have points left to spend!')
    #                 else:
    #                     self.player.strength = self.custom_points['STR']
    #                     self.player.intelligence = self.custom_points['INT']
    #                     self.player.dexterity = self.custom_points['DEX']
    #                     self.player.speed = self.custom_points['SPD']
    #                     self.player.max_mp = 3 * int(self.custom_points['MP'])
    #                     self.player.mp = self.player.max_mp
    #                     self.player.max_hp = 20 + 5 * int(self.custom_points['HP'])
    #                     self.player.hp = self.player.max_hp
    #                     del self.player.inq[0]
    #                     self.state = self.character_cleanup
    #                     self.player.dbid = self.world.db.insert_from_dict('player', self.player.to_dict())
    #                     return
    #             else:
    #                 self.player.update_output("I don't understand.")
    #         else:
    #             self.player.update_output("I don't understand.")
    #         self.display_custom_create()
    #         del self.player.inq[0]
    
