from shinymud.lib.world import *
from shinymud.models.area import *
from shinymud.commands import *
from unittest import TestCase

class TestArea(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass
