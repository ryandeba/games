from django.db import models
from django.contrib.auth.models import User

class Game(models.Model):
  date_created = models.DateTimeField(auto_now_add = True)
  date_modified = models.DateTimeField(auto_now = True)
  player_largest_army = models.ForeignKey('Player', related_name = '+')
  player_longest_road = models.ForeignKey('Player', related_name = '+')
  robber = models.ForeignKey(Hex, related_name = '+')

class Hex(models.Model):
  CHIT_CHOICES = (2,3,4,5,6,8,9,10,11,12)
  TYPE_CHOICES = ('Hills', 'Pasture', 'Mountains', 'Grain', 'Forest', 'Desert')

  game = models.ForeignKey(Game)
  position = models.IntegerField() #TODO: figure out how the position should be stored
  chit_number = models.IntegerField(choices = CHIT_CHOICES)
  type = models.CharField(max_length = 6, choices = TYPE_CHOICES)

class Player(models.Model):
  COLOR_CHOICES = ('Red', 'Blue', 'White', 'Yellow')

  game = models.ForeignKey(Game)
  user = models.ForeignKey(User, null = True)
  name = models.CharField(max_length = 50)
  color = models.CharField(max_length = 6, choices = COLOR_CHOICES)

class Road(models.Model): #each player gets 15
  player = models.ForeignKey(Player)

class City(models.Model): #each player gets 4
  player = models.ForeignKey(Player)

class Settlement(models.Model): #each player gets 5
  player = models.ForeignKey(Player)

class DevelopmentCard(models.Model):
  TYPE_CHOICES = ('Knight', 'Road Building', 'Year of plenty', 'Monopoly', 'Victory Point')

  game = models.ForeignKey(Game)
  player = models.ForeignKey(Player, null = True)
  used = models.BooleanField(default = False)
  type = models.CharField(max_length = 20, choices = TYPE_CHOICES)

class ResourceCard(models.Model):
  TYPE_CHOICES = ('Ore', 'Wheat', 'Wood', 'Sheep', 'Brick')

  game = models.ForeignKey(Game)
  player = models.ForeignKey(Player, null = True)
  type = models.CharField(max_length = 6, choices = TYPE_CHOICES)
