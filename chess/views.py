from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from chess.models import loadPendingGames, loadActiveGamesByUserID, newGame, loadGameByID
import json

@login_required
def index(request):
	return render(request, 'chess/index.html', {'username': request.user.username})

def register(request):
	username = request.POST['username']
	password = request.POST['password']

	User.objects.create_user(username = username, password = password)
	user = authenticate(username = username, password = password)
	if user is not None:
		login(request, user)
	return redirect('/')

def lobby(request):
	if request.user.is_authenticated() == False:
		return HttpResponse(status_code = 401)
	responseData = []
	for game in loadPendingGames() | loadActiveGamesByUserID(request.user.id):
		responseData.append({
			"id": game.id,
			"users": [gameUser.user.username for gameUser in game.getGameUsers()],
		})
	return HttpResponse(json.dumps(responseData), content_type="application/json")

def newGame_view(request):
	if request.user.is_authenticated() == False:
		return HttpResponse(status_code = 401)
	game = newGame()
	game.addUser(request.user)
	return HttpResponse(json.dumps({'game_id': game.id}), content_type="application/json")

def game(request, game_id):
	game = loadGameByID(game_id)
	game.addUser(request.user)
	response = {
		'id': game.id,
		'status': game.status,
		'players': [{
			'id': gameUser.id,
			'color': gameUser.getColor(),
			'username': gameUser.user.username,
		} for gameUser in game.getGameUsers()],
		'pieces': [{
			'id': piece.id,
			'player_id': piece.gameUser.id,
			'type': piece.getPieceType(),
			'position': piece.position,
		} for piece in game.getPieces()],
		'history': [{
			'id': history.id,
			'piece_id': history.piece.id,
			'fromPosition': history.fromPosition,
			'toPosition': history.toPosition,
		} for history in game.getHistory()],
	}
	return HttpResponse(json.dumps(response), content_type="application/json")

def poll(request, game_id, history_id):
	game = loadGameByID(game_id)
	response = {
		'history': [{
			'id': history.id,
			'piece_id': history.piece.id,
			'fromPosition': history.fromPosition,
			'toPosition': history.toPosition,
		} for history in game.getHistoryNewerThanHistoryID(history_id)],
		'moves': [{
			'id': move['piece'].id,
			'positions': move['positions']
		} for move in game.getAvailableMoves()]
	}
	return HttpResponse(json.dumps(response), content_type="application/json")

def movePiece(request, game_id, piece_id, position):
	game = loadGameByID(game_id)
	game.movePieceToPosition(int(piece_id), position)
	return HttpResponse(status = 200)
