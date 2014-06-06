from django.test import TestCase

from games.apps.settlersOfCatan.models import *

class GameTests(TestCase):

  def test_nothing(self):
    self.assertEqual(True, True)
