import random

from django.db import models
from django.contrib.auth.models import User

STATUS = {
    'PENDING': 'P',
    'ACTIVE': 'A',
    'FINISHED': 'F',
}

TILE_TYPE = {
    'HILLS': 'HI',
    'PASTURE': 'PA',
    'MOUNTAINS': 'MO',
    'FIELDS': 'FI',
    'FOREST': 'FO',
    'DESERT': 'DE',
}

RESOURCE_TYPE = {
    'ORE': 'OR',
    'GRAIN': 'GR',
    'LUMBER': 'LU',
    'WOOL': 'WO',
    'BRICK': 'BR',
}

DEVELOPMENT_TYPE = {
    'KNIGHT': 'KN',
    'ROAD_BUILDING': 'RB',
    'YEAR_OF_PLENTY': 'YP',
    'MONOPOLY': 'MO',
    'VICTORY_POINT': 'VP',
}

COLOR = {
    'RED': 0,
    'BLUE': 1,
    'YELLOW': 2,
    'WHITE': 3,
}

TILE_GRID = (
             (2, 1), (3, 1), (4, 1),
     (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),
     (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
     (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
             (2, 5), (3, 5), (4, 5),
)

POINT_GRID = (
                (3, 1), (4, 1),
        (2, 2), (3, 2), (4, 2), (5, 2),
(1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
(1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4),
(1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5),
(1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7),
(1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (6, 8),
(1, 9), (2, 9), (3, 9), (4, 9), (5, 9), (6, 9),
        (2,10), (3,10), (4,10), (5,10),
                (3,11), (4,11),
)

class Game(models.Model):
    status = models.CharField(
        max_length = 1,
        choices = ((value, key) for key, value in STATUS.items()),
        default = STATUS['PENDING']
    )
    player_largest_army = models.ForeignKey(
        'Player',
        related_name = '+',
        null = True
    )
    player_longest_road = models.ForeignKey(
        'Player',
        related_name = '+',
        null = True
    )
    tile_robber = models.ForeignKey(
        'Tile',
        related_name = '+',
        null = True
    )
    date_created = models.DateTimeField(auto_now_add = True)
    date_modified = models.DateTimeField(auto_now = True)

    def __unicode__(self):
        return """
                   ---
                 /     \
                /       \
            ---           ---
          /     \       /     \
         /       \     /       \
     ---           ---           ---
   /     \       /     \       /     \
  /       \     /       \     /       \
            ---           ---
  \       /     \       /     \       /
   \     /       \     /       \     /
     ---           ---           ---
         \       /     \       /
          \     /       \     /
            ---           ---
                \       /
                 \     /
                   ---"""

    def add_player(self, user = None):
        if self.status == STATUS['PENDING'] and self.player_set.count() < 4:
            if user == None:
                return self.player_set.create(game = self)
            else:
                return self.player_set.get_or_create(
                    game = self, user = user
                )[0]

    def start(self):
        self._generate_board()
        self._distribute_tokens()
        self._generate_development_cards()
        self._generate_resource_cards()
        self.status = STATUS['ACTIVE']
        self.start_next_round()

    def start_next_round(self):
        return self.round_set.create(
            game = self,
            player = self._get_next_player_turn()
        )

    def get_current_player_and_available_actions(self):
        #TODO: domestic and martime trading
        round = self.round_set.last()
        player = round.player

        actions = {
            'ROLL_DICE':
                self._building_phase_is_complete() and round.dice_have_not_been_rolled(),
            'BUY_DEVELOPMENT_CARD':
                self._building_phase_is_complete()
                and round.dice_have_been_rolled()
                # TODO: and development cards are available
                and player.can_buy_development_card(),
            'PLAY_DEVELOPMENT_CARD':
                self._building_phase_is_complete()
                and player.has_development_card_to_play(), #TODO: can't play dev cards the same turn you bought them
            'BUILD_ROAD':
                (
                    self._building_phase_is_not_complete()
                    and player.road_set.exclude(start_point_grid_x = None).count() < self.round_set.filter(player = player).count()
                ) or (
                    self._building_phase_is_complete()
                    and round.dice_have_been_rolled()
                    and player.can_buy_road()
                ),
            'BUILD_SETTLEMENT':
                (
                    not self._building_phase_is_not_complete()
                    and player.road_set.exclude(start_point_grid_x = None).count() == self.round_set.filter(player = player).count()
                    and player.settlement_set.exclude(point_grid_x = None).count() < self.round_set.filter(player = player).count()
                ) or (
                    self._building_phase_is_complete()
                    and round.dice_have_been_rolled()
                    and player.can_buy_settlement()
                ),
            'BUILD_CITY':
                self._building_phase_is_complete()
                and round.dice_have_been_rolled()
                and player.can_buy_city()
        }
        return (player, actions)

    def build_road(self, road, start_point, end_point):
        if self._can_build_road(road, start_point, end_point):
            start_x, start_y = start_point
            end_x, end_y = end_point
            road.start_point_grid_x = start_x
            road.start_point_grid_y = start_y
            road.end_point_grid_x = end_x
            road.end_point_grid_y = end_y
            road.save()
            return True
        return False

    def _can_build_road(self, road, start_point, end_point):
        return self._start_and_end_points_are_valid(start_point, end_point)

    def _start_and_end_points_are_valid(self, start_point, end_point):
        if start_point == end_point:
            return False
        start_x, start_y = start_point
        end_x, end_y = end_point
        if start_x != end_x or start_y != end_y:
            return False

    def _building_phase_is_complete(self):
        return self.round_set.count() > self.player_set.count() * 2

    def _building_phase_is_not_complete(self):
        return not self._building_phase_is_complete()

    def _get_next_player_turn(self):
        if not self._building_phase_is_complete():
            return self._get_next_player_turn_building_phase()
        if self.round_set.count() == 0:
            return self.player_set.first()
        return self._get_next_player_turn_normal_rotation()

    def _get_next_player_turn_normal_rotation(self):
        player_last_round = self.round_set.last().player
        return_next = False
        for player in self.player_set.all():
            if return_next:
                return player
            if player == player_last_round:
                return_next = True
        return self.player_set.first()

    def _get_next_player_turn_reverse_rotation(self):
        player_last_round = self.round_set.last().player
        return_next = False
        for player in self.player_set.all().reverse():
            if return_next:
                return player
            if player == player_last_round:
                return_next = True
        return self.player_set.first()

    def _get_next_player_turn_building_phase(self):
        if self.round_set.count() == 0:
            return self.player_set.first()
        if self.round_set.count() == self.player_set.count():
            return self.player_set.last()
        if self.round_set.count() < self.player_set.count():
            return self._get_next_player_turn_normal_rotation()
        return self._get_next_player_turn_reverse_rotation()

    def _generate_board(self):
        tile_types = [TILE_TYPE['HILLS']] * 3
        tile_types = tile_types + [TILE_TYPE['PASTURE']] * 4
        tile_types = tile_types + [TILE_TYPE['MOUNTAINS']] * 3
        tile_types = tile_types + [TILE_TYPE['FIELDS']] * 4
        tile_types = tile_types + [TILE_TYPE['FOREST']] * 4
        tile_types = tile_types + [TILE_TYPE['DESERT']]
        chits = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
        coordinates = list(TILE_GRID)

        random.shuffle(tile_types)
        random.shuffle(chits)

        tiles = []
        for tile_type in tile_types:
            x, y = coordinates.pop()
            tiles.append(
                Tile(
                    game = self,
                    tile_grid_x = x,
                    tile_grid_y = y,
                    type = tile_type
                )
            )
            if tile_type != TILE_TYPE['DESERT']:
                tiles[-1].chit = chits.pop()
        self.tile_set.bulk_create(tiles)

    def _distribute_tokens(self):
        for player in self.player_set.all():
            player.road_set.bulk_create(
                [Road(player = player) for x in range(15)]
            )
            player.city_set.bulk_create(
                [City(player = player) for x in range(4)]
            )
            player.settlement_set.bulk_create(
                [Settlement(player = player) for x in range(5)]
            )

    def _generate_development_cards(self):
        card_types = [DEVELOPMENT_TYPE['KNIGHT']] * 14
        card_types = card_types + [DEVELOPMENT_TYPE['ROAD_BUILDING']] * 2
        card_types = card_types + [DEVELOPMENT_TYPE['YEAR_OF_PLENTY']] * 2
        card_types = card_types + [DEVELOPMENT_TYPE['MONOPOLY']] * 2
        card_types = card_types + [DEVELOPMENT_TYPE['VICTORY_POINT']] * 5
        cards = [
            DevelopmentCard(
                game = self, type = type
            ) for type in card_types
        ]
        random.shuffle(cards)
        DevelopmentCard.objects.bulk_create(cards)

    def _generate_resource_cards(self):
        card_types = [RESOURCE_TYPE['BRICK']] * 19
        card_types = card_types + [RESOURCE_TYPE['WOOL']] * 19
        card_types = card_types + [RESOURCE_TYPE['ORE']] * 19
        card_types = card_types + [RESOURCE_TYPE['GRAIN']] * 19
        card_types = card_types + [RESOURCE_TYPE['LUMBER']] * 19
        cards = [
            ResourceCard(
                game = self, type = type
            ) for type in card_types
        ]
        random.shuffle(cards)
        ResourceCard.objects.bulk_create(cards)

class Tile(models.Model):
    game = models.ForeignKey(Game)
    tile_grid_x = models.IntegerField()
    tile_grid_y = models.IntegerField()
    chit = models.IntegerField(
        choices = ((x, x) for x in range(2, 13) if x != 7),
        null = True
    )
    type = models.CharField(
        max_length = 2,
        choices = ((value, key) for key, value in TILE_TYPE.items())
    )

class Player(models.Model):
    game = models.ForeignKey(Game)
    user = models.ForeignKey(User, null = True)
    name = models.CharField(max_length = 50)
    color = models.IntegerField(
        null = True,
        choices = ((value, key) for key, value in COLOR.items())
    )

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return self.name

class Road(models.Model):
    player = models.ForeignKey(Player)
    start_point_grid_x = models.IntegerField(null = True)
    start_point_grid_y = models.IntegerField(null = True)
    end_point_grid_x = models.IntegerField(null = True)
    end_point_grid_y = models.IntegerField(null = True)

class Settlement(models.Model):
    player = models.ForeignKey(Player)
    point_grid_x = models.IntegerField(null = True)
    point_grid_y = models.IntegerField(null = True)

class City(models.Model):
    player = models.ForeignKey(Player)
    point_grid_x = models.IntegerField(null = True)
    point_grid_y = models.IntegerField(null = True)

class DevelopmentCard(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player, null = True)
    played = models.BooleanField(default = False)
    type = models.CharField(
        max_length = 2,
        choices = ((value, key) for key, value in DEVELOPMENT_TYPE.items())
    )

class ResourceCard(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player, null = True)
    type = models.CharField(
        max_length = 2,
        choices = ((value, key) for key, value in RESOURCE_TYPE.items())
    )

class Round(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    die_value_1 = models.IntegerField(null = True)
    die_value_2 = models.IntegerField(null = True)
    date_created = models.DateTimeField(auto_now_add = True)
    date_modified = models.DateTimeField(auto_now = True)

    class Meta:
        ordering = ['date_created']

    def dice_have_been_rolled(self):
        return self.die_value_1 != None and self.die_value_2 != None

    def dice_have_not_been_rolled(self):
        return not self.dice_have_been_rolled()
