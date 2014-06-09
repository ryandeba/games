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
        #building phase
        self.assertEqual(self.player1, self.game.round_set.last().player)
        self.assertEqual(self.player2, self.game.start_next_round().player)
        self.assertEqual(self.player3, self.game.start_next_round().player)
        self.assertEqual(self.player3, self.game.start_next_round().player)
        self.assertEqual(self.player2, self.game.start_next_round().player)
        self.assertEqual(self.player1, self.game.start_next_round().player)

        #normal play
        self.assertEqual(self.player1, self.game.start_next_round().player)
        self.assertEqual(self.player2, self.game.start_next_round().player)
        self.assertEqual(self.player3, self.game.start_next_round().player)
        self.assertEqual(self.player1, self.game.start_next_round().player)
        self.assertEqual(self.player2, self.game.start_next_round().player)
        self.assertEqual(self.player3, self.game.start_next_round().player)

class Game_get_available_actions(TestCase):

    def setUp(self):
        self.game = Game.objects.create()
        self.player1 = self.game.add_player()
        self.player2 = self.game.add_player()
        self.player3 = self.game.add_player()
        self.game.start()

class Game_get_current_player_and_available_actions(TestCase):

    def setUp(self):
        self.game = Game.objects.create()
        self.player1 = self.game.add_player()
        self.player2 = self.game.add_player()
        self.player3 = self.game.add_player()
        self.game.start()

    def test_building_phase(self):
        player, actions = self.game.get_current_player_and_available_actions()
        self.assertEqual(False, actions['ROLL_DICE'])
        self.assertEqual(False, actions['BUY_DEVELOPMENT_CARD'])
        self.assertEqual(False, actions['PLAY_DEVELOPMENT_CARD'])
        self.assertEqual(True, actions['BUILD_ROAD'])
        self.assertEqual(False, actions['BUILD_SETTLEMENT'])
        self.assertEqual(False, actions['BUILD_CITY'])

class Game_build_road(TestCase):

    def setUp(self):
        self.game = Game.objects.create()
        self.player1 = self.game.add_player()
        self.player2 = self.game.add_player()
        self.player3 = self.game.add_player()
        self.game.start()

    def test_road_coordinates_are_set(self):
        road = self.player1.road_set.first()
        self.game.build_road(road, (3, 5), (4, 5))
        self.assertEqual(3, road.start_point_grid_x)
        self.assertEqual(5, road.start_point_grid_y)
        self.assertEqual(4, road.end_point_grid_x)
        self.assertEqual(5, road.end_point_grid_y)

    def test_invalid_coordinates_returns_false(self):
        road = self.player1.road_set.first()
        #self.assertEqual(False, self.game.build_road(road, 3, 2, 4, 2))
        self.assertEqual(False, self.game.build_road(road, (3, 5), (3, 5)))
