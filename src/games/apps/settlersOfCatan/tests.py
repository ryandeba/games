from django.test import TestCase

from games.apps.settlersOfCatan.models import *

class Game_start(TestCase):

    def setUp(self):
        self.game = Game.objects.create()
        self.game.add_player()
        self.game.add_player()
        self.game.start()

    def test_tiles_are_created(self):
        self.assertEqual(19, self.game.tile_set.count())

    def test_roads_are_distributed(self):
        player1 = self.game.player_set.all()[0]
        player2 = self.game.player_set.all()[1]
        self.assertEqual(15, player1.road_set.count())
        self.assertEqual(15, player2.road_set.count())

    def test_cities_are_distributed(self):
        player1 = self.game.player_set.all()[0]
        player2 = self.game.player_set.all()[1]
        self.assertEqual(4, player1.city_set.count())
        self.assertEqual(4, player2.city_set.count())

    def test_settlements_are_distributed(self):
        player1 = self.game.player_set.all()[0]
        player2 = self.game.player_set.all()[1]
        self.assertEqual(5, player1.settlement_set.count())
        self.assertEqual(5, player2.settlement_set.count())

    def test_game_is_active(self):
        self.assertEqual(STATUS['ACTIVE'], self.game.status)
