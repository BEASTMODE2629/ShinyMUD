from shinymud.lib.world import *
from shinymud.data.config import *
from shinymud.lib.registers import CommandRegister
def get_permission_names(perm_int):
    """Takes an integer representing a set of permissions and returns a list
    of corresponding permission names."""
    pms = {'God': 16, 'Admin': 8, 'Builder': 2, 'Player': 1, 'DM': 4}
    perm_list = []
    for key, value in pms.items():
        if perm_int & value:
            perm_list.append(key)
    return perm_list


# Create the list of command-related Help Pages
command_help = CommandRegister()


class BaseCommand(object):
    required_permissions = PLAYER
    help = ("We Don't have a help page for this command yet."
    )
    def __init__(self, player, args, alias):
        self.args = args
        self.pc = player
        self.alias = alias
        self.world = World.get_world()
        self.allowed = True
        if not (self.pc.permissions & GOD):
            if not (self.pc.permissions & self.required_permissions):
                self.allowed = False
    
    def run(self):
        if self.allowed:
            self.execute()
        else:
            self.pc.update_output("You don't have the authority to do that!\n")
    
    def personalize(self, message, actor, target=None):
        """Personalize an action message for a player.
        
        This function replaces certain keywords in generic messages with 
        player-specific data to make the message more personal. Below is a list
        of the keywords that will be replaced if they are found in the message:
        
        #actor - replaced with the name of the actor (player committing the action)
        #a_she/he - replaced with the gender-specific pronoun of the actor
        #a_her/him - replaced with the gender-specific pronoun of the actor (grammatical alternative)
        #a_hers/his - replace with the gender-specific possessive-pronoun of the actor
        #a_her/his - replace with the gender-specific possessive-pronoun of the actor (grammatical alternative)
        #a_self - replace with the gender-specific reflexive pronoun of the actor (himself/herself/itself)
        
        #target - replace with the name of the target (player being acted upon)
        #t_she/he - replaced with the gender-specific pronoun of the target
        #t_her/him - replace with the gender-specific pronoun of the target (grammatical alternative)
        #t_hers/his - replace with a gender-specific possessive-pronoun of the target
        #t_her/his - replace with the gender-specific possessive-pronoun of the target (grammatical alternative)
        #t_self - replace with the gender-specific reflexive pronoun of the target (himself/herself/itself)
        """
                                                             #Examples:
        she_pronouns = {'female': 'she', 'male': 'he', 'neutral': 'it'} #she/he looks tired
        her_pronouns = {'female': 'her', 'male': 'him', 'neutral': 'it'} #Look at her/him.
        hers_possesive = {'female': 'hers', 'male': 'his', 'neutral': 'its'} #That thing is hers/his.
        her_possesive = {'female': 'her', 'male': 'his', 'neutral': 'its'} #Person lost her/his thingy.
        reflexives = {'female': 'herself', 'male': 'himself', 'neutral': 'itself'}
        
        message = message.replace('#actor', actor.fancy_name())
        message = message.replace('#a_she/he', she_pronouns.get(actor.gender)) 
        message = message.replace('#a_her/him', her_pronouns.get(actor.gender)) 
        message = message.replace('#a_hers/his', hers_possesive.get(actor.gender))
        message = message.replace('#a_her/his', her_possesive.get(actor.gender))
        message = message.replace('#a_self', reflexives.get(actor.gender))
        
        # We should always have an actor, but we don't always have a target.
        if target:
            message = message.replace('#target', target.fancy_name())
            message = message.replace('#t_she/he', she_pronouns.get(target.gender))
            message = message.replace('#t_her/him', her_pronouns.get(target.gender))
            message = message.replace('#t_hers/his', hers_possesive.get(target.gender))
            message = message.replace('#t_her/his', her_possesive.get(target.gender))
            message = message.replace('#t_self', reflexives.get(target.gender))
        return message
    

