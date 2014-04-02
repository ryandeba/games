from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.timezone import utc
from chess.models import loadPendingGames, loadActiveGamesByUserID, newGame, loadGameByID
import json, time, datetime

def datetimeToEpoch(datetime):
	return str(time.mktime(datetime.timetuple()) + float("0.%s" % datetime.microsecond))

def timestampToDatetime(timestamp):
	return datetime.datetime.utcfromtimestamp(float(timestamp)).replace(tzinfo = utc)

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

	datetimeLastUpdated = timestampToDatetime(request.GET.get("lastUpdated", "0"))

	players = [{
		'id': gameUser.id,
		'color': gameUser.getColor(),
		'username': gameUser.user.username,
	} for gameUser in game.getGameUsersModifiedSince(datetimeLastUpdated)]

	pieces = [{
		'id': piece.id,
		'player_id': piece.gameUser.id,
		'type': piece.getPieceType(),
		'position': piece.position,
	} for piece in game.getPiecesModifiedSince(datetimeLastUpdated)]

	response = {}
	if (
		datetimeToEpoch(game.datetimeLastModified) > datetimeToEpoch(datetimeLastUpdated)
		or len(players) > 0
		or len(pieces) > 0
	):
		response = {
			'status': game.status,
			'players': players,
			'pieces': pieces,
			'moves': [{
				'id': move['piece'].id,
				'positions': move['positions']
			} for move in game.getAvailableMoves() if move['piece'].gameUser.user == request.user],
			'lastUpdated': datetimeToEpoch(datetime.datetime.utcnow()),
			'currentturn_player_id': game.getGameUserCurrentTurn().id,
		}
	return HttpResponse(json.dumps(response), content_type="application/json")

def movePiece(request, game_id, piece_id, position):
	game = loadGameByID(game_id)
	game.movePieceToPosition(int(piece_id), position)
	return HttpResponse(status = 200)
