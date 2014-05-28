from django.shortcuts import render
from django.http import HttpResponse
from django.utils.dateformat import format
from django.utils.timezone import utc
from django.db.models import Q

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from games.apps.cardsAgainstHumanity.models import User, Game, Card

import json, time, datetime

@login_required
def index(request):
	return render(request, 'game/index.html', {'username': request.user.username})

def lobby(request):
	responseData = []
	for game in Game.objects.filter(active = 0).order_by("-gameplayer__datetimeCreated","-id")[:50]:
		responseData.append({
			"id": game.id,
			"numberOfPlayers": game.getNumberOfPlayers(),
			"secondsSinceLastPlayerJoined": game.getSecondsSinceLastPlayerJoined(),
		})
	for game in Game.objects.filter(active = 1, gameplayer__user_id = request.user.id):
		responseData.append({
			"id": game.id,
			"numberOfPlayers": game.getNumberOfPlayers(),
			"secondsSinceLastPlayerJoined": game.getSecondsSinceLastPlayerJoined(),
		})
	return HttpResponse(json.dumps(responseData), content_type="application/json")

def newGame(request):
	game = Game.objects.create(expansionList = request.GET.get("expansionlist", ""))

	responseData = { "id": game.id, }
	return HttpResponse(json.dumps(responseData), content_type="application/json")

def addBot(request, game_id):
	Game.objects.get(id = game_id).addBot()
	return HttpResponse(status = 200)

def startGame(request, game_id):
	Game.objects.get(id = game_id).startGame()
	return HttpResponse(status = 200)

def game(request, game_id):
	game = Game.objects.get(id = game_id)
	game.addPlayer(request.user)
	game.applyAllAvailableGameActions()
	gamePlayer = game.gameplayer_set.all().filter(user = request.user).first()

	responseData = getGameJSON(
		game = game,
		thisPlayer = gamePlayer,
		datetimeLastUpdated = timestampToDatetime(request.GET.get("lastUpdated", "0"))
	)
	return HttpResponse(json.dumps(responseData), content_type="application/json")

def submitAnswer(request, game_id, card_id):
	game = Game.objects.get(id = game_id)
	gamePlayer = game.gameplayer_set.get(game = game, user = request.user)
	gameCard = game.gamecard_set.get(game = game, gamePlayer = gamePlayer, card_id = card_id)
	if game.gamePlayerSubmitsAnswerCard(gamePlayer, gameCard):
		return HttpResponse(status = 200)
	return HttpResponse(status = 403)

def chooseWinner(request, game_id, card_id):
	game = Game.objects.get(id = game_id)
	gameCard = game.gamecard_set.get(game = game, card_id = card_id)
	gamePlayer = game.gameplayer_set.get(game = game, user = request.user)
	game.gamePlayerPicksWinningAnswerCard(gamePlayer, gameCard)
	return HttpResponse(status = 200)

def submitMessage(request, game_id):
	message = request.GET.get("message", "")
	if len(message.strip()) == 0:
		return HttpResponse(status = 400)
	game = Game.objects.get(id = game_id)
	gamePlayer = game.gameplayer_set.get(game = game, user = request.user)
	game.gamemessage_set.create(game = game, gamePlayer = gamePlayer, message = message)
	return HttpResponse(status = 200)

def getGameJSON(game, thisPlayer, datetimeLastUpdated):
	thisPlayersAnswerCards = [
			{
				"card_id": gameCard.card.id,
				"text": gameCard.card.text
			} for gameCard in game.gamecard_set.filter(game = game, gamePlayer = thisPlayer, datetimeLastModified__gte = datetimeLastUpdated).exclude(gamePlayer_id = None)
		]

	gamePlayers = [
			{
				"id": gamePlayer.id,
				"name": gamePlayer.getName(),
				"points": gamePlayer.getPoints(),
			} for gamePlayer in game.gameplayer_set.all().filter(datetimeLastModified__gte = datetimeLastUpdated).order_by("id").distinct()
		]

	gameRounds = [
			{
				"id": gameRound.id,
				"gamePlayerQuestioner_id": gameRound.gamePlayerQuestioner_id,
				"question": gameRound.gameCardQuestion.card.text,
				"isComplete": gameRound.isComplete(),
				"allAnswersHaveBeenSubmitted": gameRound.allAnswersHaveBeenSubmitted(),
				"answers": [
					{
						"text": answer.gameCard.card.text,
						"gameplayer_id": answer.gamePlayer.id,
						"card_id": answer.gameCard.card.id,
						"winner": answer.isWinner(),
					} for answer in gameRound.gameroundanswer_set.all().filter(datetimeLastModified__gte = datetimeLastUpdated)
				],
			} for gameRound in game.gameround_set.all().filter(Q(datetimeLastModified__gte = datetimeLastUpdated) | Q(gameroundanswer__datetimeLastModified__gte = datetimeLastUpdated)).order_by("id").distinct()
		]

	gameMessages = [
		{
			"id": gameMessage.id,
			"gameplayer_id": gameMessage.gamePlayer_id,
			"message": gameMessage.message,
		} for gameMessage in game.gamemessage_set.all().filter(datetimeLastModified__gte = datetimeLastUpdated)
	]

	if (
		datetimeToEpoch(game.datetimeLastModified) < datetimeToEpoch(datetimeLastUpdated)
		and len(thisPlayersAnswerCards) == 0
		and len(gamePlayers) == 0
		and len(gameRounds) == 0
		and len(gameMessages) == 0
	):
		return {}
	result = {
		"lastUpdated": datetimeToEpoch(datetime.datetime.utcnow()),
		"id": game.id,
		"active": game.active,
		"thisPlayersAnswerCards": thisPlayersAnswerCards,
		"gamePlayers": gamePlayers,
		"gameRounds": gameRounds,
		"gameMessages": gameMessages,
	}
	return result

def datetimeToEpoch(datetime):
	return str(time.mktime(datetime.timetuple()) + float("0.%s" % datetime.microsecond))

def timestampToDatetime(timestamp):
	return datetime.datetime.utcfromtimestamp(float(timestamp)).replace(tzinfo = utc)
