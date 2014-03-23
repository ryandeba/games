from django.shortcuts import render
from django.http import HttpResponse

from chess.models import Game

import json

def index(request):
	return render(request, 'chess/index.html', {})
