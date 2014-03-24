from django.shortcuts import render
from django.http import HttpResponse

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from chess.models import Game
import json

@login_required
def index(request):
	return render(request, 'chess/index.html', {})
