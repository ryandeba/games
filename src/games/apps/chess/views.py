from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.timezone import utc
from games.apps.chess.models import load_pending_games, load_active_games_by_user_id, new_game, load_game_by_id
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
	for game in load_pending_games() | load_active_games_by_user_id(request.user.id):
		responseData.append({
			"id": game.id,
			"users": [gameUser.user.username for gameUser in game.get_gameusers()],
		})
	return HttpResponse(json.dumps(responseData), content_type="application/json")

def newGame_view(request):
	if request.user.is_authenticated() == False:
		return HttpResponse(status_code = 401)
	game = new_game()
	game.add_user(request.user)
	return HttpResponse(json.dumps({'game_id': game.id}), content_type="application/json")

def game(request, game_id):
	game = load_game_by_id(game_id)
	game.add_user(request.user)

	datetimeLastUpdated = timestampToDatetime(request.GET.get("lastUpdated", "0"))

	players = [{
		'id': gameUser.id,
		'color': gameUser.get_color(),
		'username': gameUser.user.username,
	} for gameUser in game.get_gameusers_modified_since(datetimeLastUpdated)]

	pieces = [{
		'id': piece.id,
		'player_id': piece.gameUser.id,
		'type': piece.get_type(),
		'position': piece.position,
	} for piece in game.get_pieces_modified_since(datetimeLastUpdated)]

	history = [{
		'id': hist.id,
		'piece_id': hist.piece_id,
		'from': hist.fromPosition,
		'to': hist.toPosition,
	} for hist in game.get_history_modified_since(datetimeLastUpdated)]

	response = {}
	if (
		datetimeToEpoch(game.datetimeLastModified) > datetimeToEpoch(datetimeLastUpdated)
		or len(players) > 0
		or len(pieces) > 0
	):
		game.update_status()
		response = {
			'status': game.status,
			'players': players,
			'pieces': pieces,
			'history': history,
			'moves': [{
				'id': move['piece'].id,
				'positions': move['positions']
			} for move in game.get_available_moves() if move['piece'].gameUser.user == request.user],
			'lastUpdated': datetimeToEpoch(datetime.datetime.utcnow()),
			'currentturn_player_id': game.get_gameuser_current_turn().id,
			'winner_player_id': None,
		}

		winner = game.get_winner_gameuser()
		if winner:
			response['winner_player_id'] = winner.id

	return HttpResponse(json.dumps(response), content_type="application/json")

def movePiece(request, game_id, piece_id, position):
	game = load_game_by_id(game_id)
	game.move_piece_to_position(int(piece_id), position)
	return HttpResponse(status = 200)
