from django.db import models
from django.contrib.auth.models import User

import random

STATUS = {
    'PENDING' : 'P',
    'ACTIVE' : 'A',
    'FINISHED' : 'F',
}

TILE_TYPE = {
    'HILLS' : 'HI',
    'PASTURE' : 'PA',
    'MOUNTAINS' : 'MO',
    'FIELDS' : 'FI',
    'FOREST' : 'FO',
    'DESERT' : 'DE',
}

RESOURCE_TYPE = {
    'ORE' : 'OR',
    'WHEAT' : 'WH',
    'WOOD' : 'WO',
    'SHEEP' : 'SH',
    'BRICK' : 'BR',
}

DEVELOPMENT_TYPE = {
    'KNIGHT' : 'KN',
    'ROAD_BUILDING' : 'RB',
    'YEAR_OF_PLENTY' : 'YP',
    'MONOPOLY' : 'MO',
    'VICTORY_POINT' : 'VP',
}

COLOR = {
    'RED' : 0,
    'BLUE' : 1,
    'YELLOW' : 2,
    'WHITE' : 3,
}

class Game(models.Model):
    status = models.CharField(max_length = 1, choices = ((value, key) for key, value in STATUS.items()))
    player_largest_army = models.ForeignKey('Player', related_name = '+', null = True)
    player_longest_road = models.ForeignKey('Player', related_name = '+', null = True)
    tile_robber = models.ForeignKey('Tile', related_name = '+', null = True)
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
        #if self.status != STATUS['PENDING'] and self.player_set.count() < 4:
        if user == None:
            return self.player_set.create(game = self)
        else:
            return self.player_set.get_or_create(game = self, user = user)

    def start(self):
        self._generate_board()
        self._distribute_tokens()
        self.status = STATUS['ACTIVE']
        self.save()

    def _generate_board(self):
        tile_types = [TILE_TYPE['HILLS']] * 3 + [TILE_TYPE['PASTURE']] * 4 + [TILE_TYPE['MOUNTAINS']] * 3 + [TILE_TYPE['FIELDS']] * 4 + [TILE_TYPE['FOREST']] * 4 + [TILE_TYPE['DESERT']]
        chits = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
        coordinates = [
            (1, 2), (1, 3), (1, 4),
            (2, 1), (2, 2), (2, 3), (2, 4),
            (3, 1), (3, 2), (3, 3), (3, 4), (3, 5),
            (4, 1), (4, 2), (4, 3), (4, 4),
            (5, 2), (5, 3), (5, 4),
        ]

        random.shuffle(tile_types)
        random.shuffle(chits)

        tiles = []
        for tile_type in tile_types:
            x, y = coordinates.pop()
            tiles.append(Tile(game = self, tile_grid_x = x, tile_grid_y = y, type = tile_type))
            if tile_type != TILE_TYPE['DESERT']:
                tiles[-1].chit = chits.pop()

        self.tile_set.bulk_create(tiles)

    def _distribute_tokens(self):
        for player in self.player_set.all():
            player.road_set.bulk_create([ Road(player = player) for x in range(15) ])
            player.city_set.bulk_create([ City(player = player) for x in range(4) ])
            player.settlement_set.bulk_create([ Settlement(player = player) for x in range(5) ])

class Tile(models.Model):
    game = models.ForeignKey(Game)
    tile_grid_x = models.IntegerField()
    tile_grid_y = models.IntegerField()
    chit = models.IntegerField(choices = ((x, x) for x in range(2, 7) + range(8, 13)), null = True)
    type = models.CharField(max_length = 2, choices = ((value, key) for key, value in TILE_TYPE.items()))

class Player(models.Model):
    game = models.ForeignKey(Game)
    user = models.ForeignKey(User, null = True)
    name = models.CharField(max_length = 50)
    color = models.IntegerField(null = True, choices = ((value, key) for key, value in COLOR.items()))

class Road(models.Model):
    player = models.ForeignKey(Player)
    start_point_grid_x = models.IntegerField(null = True)
    start_point_grid_y = models.IntegerField(null = True)
    end_point_grid_x = models.IntegerField(null = True)
    end_point_grid_y = models.IntegerField(null = True)

class City(models.Model):
    player = models.ForeignKey(Player)
    point_grid_x = models.IntegerField(null = True)
    point_grid_y = models.IntegerField(null = True)

class Settlement(models.Model):
    player = models.ForeignKey(Player)
    point_grid_x = models.IntegerField(null = True)
    point_grid_y = models.IntegerField(null = True)

class DevelopmentCard(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player, null = True)
    used = models.BooleanField(default = False)
    type = models.CharField(max_length = 2, choices = ((value, key) for key, value in DEVELOPMENT_TYPE.items()))

class ResourceCard(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player, null = True)
    type = models.CharField(max_length = 2, choices = ((value, key) for key, value in RESOURCE_TYPE.items()))
