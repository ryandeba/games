from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

SECONDS_TO_WAIT_BETWEEN_ROUNDS = 10
MAXIMUM_NUMBER_OF_PLAYERS = 6
NUMBER_OF_POINTS_NEEDED_TO_WIN = 10

class Card(models.Model):
	cardType = models.CharField(max_length = 1)
	text = models.CharField(max_length = 200)
	numberOfAnswers = models.IntegerField(default = 1)
	expansion = models.CharField(max_length = 100)

	def __unicode__(self):
		return self.cardType + " | " + self.text

class Name(models.Model):
	name = models.CharField(max_length = 50)

	def __unicode__(self):
		return self.name

class GameManager(models.Manager):
	def create(self, active = 0, expansionList = ""):
		game = super(GameManager, self).create(active = active, expansionList = expansionList)
		game.addCards()
		return game

class Game(models.Model):
	active = models.IntegerField(default = 0) #0 - lobby, 1 - active, 2 - finished #TODO: rename this column to status or something
	datetimeLastModified = models.DateTimeField(auto_now = True)
	expansionList = models.CharField(max_length = 200)
	objects = GameManager()

	def __unicode__(self):
		return "ID: %s | Active: %s | Players: %s" % (self.id, self.active, self.getNumberOfPlayers())

	def addCards(self):
		self.gamecard_set.bulk_create(
			[
				GameCard(game = self, card = card)
				for card in Card.objects.filter(expansion__in = ("Base," + self.expansionList).split(","), numberOfAnswers__lt = 2)
			]
		)
		return

	def getNumberOfPlayers(self):
		return self.gameplayer_set.all().count()

	def getSecondsSinceLastPlayerJoined(self):
		lastPlayerToJoin = self.gameplayer_set.all().order_by("-id").first()
		if lastPlayerToJoin:
			return (timezone.now() - lastPlayerToJoin.datetimeCreated).total_seconds()
		else:
			return 0

	def addPlayer(self, user):
		if self.canAddAnotherPlayer():
			self.gameplayer_set.get_or_create(game = self, user = user)
		return

	def addBot(self):
		if self.canAddAnotherPlayer():
			self.gameplayer_set.create(game = self)
		return

	def canAddAnotherPlayer(self):
		return self.active == 0 and self.getNumberOfPlayers() < MAXIMUM_NUMBER_OF_PLAYERS

	def applyAllAvailableGameActions(self):
		self.finishGame()
		self.takeAllBotActions()
		self.newRound()

	def finishGame(self):
		for gamePlayer in self.gameplayer_set.all():
			if gamePlayer.getPoints() >= NUMBER_OF_POINTS_NEEDED_TO_WIN:
				self.active = 2
				self.save()
				return

	def startGame(self):
		if self.isReadyToStart():
			self.active = 1
			self.save()
			self.newRound()
		return

	def isReadyToStart(self):
		return self.active == 0 and self.getNumberOfPlayers() > 2

	def dealAnswerCards(self):
		unusedAnswerCards = list(self.gamecard_set.all().filter(card__cardType = "A", gamePlayer = None, gameroundanswer = None).order_by("?"))
		for gamePlayer in self.gameplayer_set.all():
			while len(self.gamecard_set.all().filter(gamePlayer = gamePlayer)) < 10:
				gameCard = unusedAnswerCards.pop()
				gameCard.gamePlayer = gamePlayer
				gameCard.save()

	def getRandomUnusedQuestionCard(self):
		return self.gamecard_set.all().filter(card__cardType = "Q", gamePlayer = None, gameround = None).order_by("?").first()

	def newRound(self):
		if self.isReadyToStartNewRound():
			self.gameround_set.create(
				game = self,
				gameCardQuestion = self.getRandomUnusedQuestionCard(),
				gamePlayerQuestioner = self.getNextGameRoundGamePlayerQuestioner()
			)
			self.dealAnswerCards()
		return

	def isReadyToStartNewRound(self):
		if self.active != 1:
			return False
		gameRound = self.getMostRecentRound()
		if gameRound == None:
			return True
		if (gameRound.isComplete()
				and (timezone.now() - gameRound.getDatetimeLastModified()).total_seconds() >= SECONDS_TO_WAIT_BETWEEN_ROUNDS
		):
			return True
		return False

	def getMostRecentRound(self):
		return self.gameround_set.order_by("-id").first()

	def getNextGameRoundGamePlayerQuestioner(self):
		if self.gameround_set.all().count() > 0:
			lastGameRound = self.getMostRecentRound()
			lastGamePlayerQuestioner = lastGameRound.gamePlayerQuestioner

			gamePlayers = self.gameplayer_set.all().order_by("id")
			foundTheLastPlayer = False
			for gamePlayer in gamePlayers:
				if foundTheLastPlayer:
					return gamePlayer
				if gamePlayer.id == lastGamePlayerQuestioner.id:
					foundTheLastPlayer = True
			return gamePlayers[0]
		else:
			return self.gameplayer_set.all().order_by("?").first()

	def gamePlayerSubmitsAnswerCard(self, gamePlayer, gameCard):
		currentRound = self.getMostRecentRound()
		if (currentRound
				and currentRound.isComplete() == False
				and currentRound.gamePlayerQuestioner.id != gamePlayer.id
				and currentRound.gameroundanswer_set.all().filter(gamePlayer = gamePlayer).count() == 0
		):
			gameCard.gamePlayer = None
			gameCard.save()
			currentRound.gameroundanswer_set.create(gameRound = currentRound, gameCard = gameCard, gamePlayer = gamePlayer)
			return True
		return False

	def gamePlayerPicksWinningAnswerCard(self, gamePlayer, gameCard):
		gameRound = self.getMostRecentRound()
		if (gameRound
				and gameRound.isComplete() == False
				and gameRound.allAnswersHaveBeenSubmitted()
				and gameRound.gamePlayerQuestioner_id == gamePlayer.id
		):
			gameRoundAnswer = gameRound.gameroundanswer_set.get(gameRound = gameRound, gameCard = gameCard)
			gameRoundAnswer.winner = 1
			gameRoundAnswer.save()
			return True
		return False

	def takeAllBotActions(self):
		currentRound = self.getMostRecentRound()
		if currentRound:
			for gamePlayer in self.gameplayer_set.all().filter(user = None):
				self.gamePlayerSubmitsAnswerCard(gamePlayer, gamePlayer.getRandomAnswerCard())
				if currentRound.allAnswersHaveBeenSubmitted():
					self.gamePlayerPicksWinningAnswerCard(gamePlayer, currentRound.getRandomGameRoundAnswer().gameCard)
		return True

class GamePlayer(models.Model):
	game = models.ForeignKey(Game)
	user = models.ForeignKey(User, null = True)
	name = models.CharField(max_length = 50)
	datetimeCreated = models.DateTimeField(auto_now_add = True)
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def getName(self):
		if self.user:
			return self.user.username
		if len(self.name) == 0:
			self.name = Name.objects.all().order_by("?").first().name
			self.save()
		return self.name

	def getPoints(self):
		return self.gameroundanswer_set.all().filter(winner = 1).count()

	def getRandomAnswerCard(self):
		return self.gamecard_set.all().order_by("?").first()

class GameCard(models.Model):
	game = models.ForeignKey(Game)
	card = models.ForeignKey(Card)
	gamePlayer = models.ForeignKey(GamePlayer, null = True)
	datetimeLastModified = models.DateTimeField(auto_now = True)

class GameRound(models.Model):
	game = models.ForeignKey(Game)
	gameCardQuestion = models.ForeignKey(GameCard)
	gamePlayerQuestioner = models.ForeignKey(GamePlayer)
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def isComplete(self):
		return self.gameroundanswer_set.all().filter(winner = 1).count() > 0

	def allAnswersHaveBeenSubmitted(self):
		for gamePlayer in self.game.gameplayer_set.all().exclude(id = self.gamePlayerQuestioner_id):
			if self.gameroundanswer_set.all().filter(gamePlayer = gamePlayer).count() == 0:
				return False
		return True

	def getRandomGameRoundAnswer(self):
		return self.gameroundanswer_set.all().order_by("?").first()

	def getDatetimeLastModified(self):
		gameRoundAnswer = self.gameroundanswer_set.all().order_by("-datetimeLastModified").first()
		if gameRoundAnswer:
			return gameRoundAnswer.datetimeLastModified
		return timezone.now()

class GameRoundAnswer(models.Model):
	gameRound = models.ForeignKey(GameRound)
	gameCard = models.ForeignKey(GameCard)
	gamePlayer = models.ForeignKey(GamePlayer) #this might seem weird in conjunction with gameCard, but gameCard gets unassigned from the gamePlayer when added
	winner = models.IntegerField(default = 0)
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def isWinner(self):
		return self.winner == 1

class GameMessage(models.Model):
	game = models.ForeignKey(Game)
	gamePlayer = models.ForeignKey(GamePlayer)
	message = models.CharField(max_length = 500)
	datetimeLastModified = models.DateTimeField(auto_now = True)
