from django.test import TestCase

from games.apps.settlersOfCatan.models import *

class Game_add_player(TestCase):

    def setUp(self):
        self.game = Game.objects.create()
        self.user1 = User.objects.create(username = 'user1')
        self.user2 = User.objects.create(username = 'user2')

    def test_players_with_no_user_are_added(self):
        player1 = self.game.add_player()
        player2 = self.game.add_player()
        self.assertNotEqual(player1, player2)
        self.assertEqual(True, player1 in self.game.player_set.all())
        self.assertEqual(True, player2 in self.game.player_set.all())

    def test_players_with_user_are_added(self):
        player1 = self.game.add_player(self.user1)
        player2 = self.game.add_player(self.user2)
        self.assertNotEqual(player1, player2)
        self.assertEqual(True, player1 in self.game.player_set.all())
        self.assertEqual(True, player2 in self.game.player_set.all())

    def test_users_cannot_be_added_more_than_once(self):
        player1 = self.game.add_player(self.user1)
        player2 = self.game.add_player(self.user1)
        self.assertEqual(player1, player1)
        self.assertEqual(1, self.game.player_set.count())

    def test_users_not_added_when_status_not_pending(self):
        self.game.status = STATUS['ACTIVE']
        player1 = self.game.add_player()
        self.assertEqual(None, player1)
        self.assertEqual(0, self.game.player_set.count())

    def test_users_not_added_when_player_limit_exceeded(self):
        for x in range(10):
            self.game.add_player()
        self.assertEqual(4, self.game.player_set.count())

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

    def test_development_cards(self):
        self.assertEqual(25, self.game.developmentcard_set.count())

    def test_resource_cards(self):
        self.assertEqual(95, self.game.resourcecard_set.count())

class Game_start_next_round(TestCase):

    def setUp(self):
        self.game = Game.objects.create()
        self.player1 = self.game.add_player()
        self.player2 = self.game.add_player()
        self.player3 = self.game.add_player()
        self.game.start()

    def test_player_order(self):
        pass
