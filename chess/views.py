from django.shortcuts import render
from django.http import HttpResponse

from chess.models import GameService

import json

gameService = GameService()

def index(request):
	return HttpResponse(status = 200)
