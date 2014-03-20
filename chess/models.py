from django.db import models
from django.contrib.auth.models import User

GAMESTATUS = {"PENDING": 0, "ACTIVE": 1, "FINISHED": 2}
COLOR = {"BLACK": 0, "WHITE": 1}
PIECETYPE = {
	"PAWN": 0,
	"ROOK": 1,
	"KNIGHT": 2,
	"BISHOP": 3,
	"QUEEN": 4,
	"KING": 5
}
XCOORDINATES = ["A","B","C","D","E","F","G","H"]

def newGame():
	game = Game.objects.create(status = GAMESTATUS["PENDING"])
	return game

def newUser(username):
	return User.objects.create(username = username)

def newGameUser(game, user, color):
	return GameUser.objects.create(game = game, user = user, color = color)

def newPiece(gameUser, position, type):
	return Piece.objects.create(gameUser = gameUser, position = position, type = PIECETYPE[type])

def newHistory(piece, fromPosition, toPosition):
	return History.objects.create(piece = piece, fromPosition = fromPosition, toPosition = toPosition)

def loadGameByID(id):
	return Game.objects.get(id = id)

def loadGameUsersByGame(game):
	return GameUser.objects.filter(game = game)

def loadPiecesByGame(game):
	return resolvePieceToSpecificType(Piece.objects.filter(gameUser__game = game))

def loadPiecesByGameUser(gameUser):
	return resolvePieceToSpecificType(Piece.objects.filter(gameUser = gameUser))

def loadHistoryByGame(game):
	return History.objects.filter(piece__gameUser__game = game)

def loadHistoryByPiece(piece):
	return History.objects.filter(piece = piece)

def getHistoryCountByPiece(piece):
	return History.objects.filter(piece = piece).count()

def getPositionByOffset(startingPosition, offsetX, offsetY):
	x, y = convertPositionToCoordinates(startingPosition)
	if 1 <= x + offsetX <= 8 and 1 <= y + offsetY <= 8:
		return convertCoordinatesToPosition((x + offsetX, y + offsetY))
	return ""

def resolvePieceToSpecificType(pieces):
	result = []
	for piece in pieces:
		if piece.type == PIECETYPE["PAWN"]:
			actualPiece = Pawn()
		elif piece.type == PIECETYPE["ROOK"]:
			actualPiece = Rook()
		elif piece.type == PIECETYPE["KNIGHT"]:
			actualPiece = Knight()
		elif piece.type == PIECETYPE["BISHOP"]:
			actualPiece = Bishop()
		elif piece.type == PIECETYPE["QUEEN"]:
			actualPiece = Queen()
		elif piece.type == PIECETYPE["KING"]:
			actualPiece = King()
		actualPiece.id = piece.id
		actualPiece.gameUser = piece.gameUser
		actualPiece.position = piece.position
		actualPiece.type = piece.type
		result.append(actualPiece)
	return result

def convertPositionToCoordinates(position):
	return (XCOORDINATES.index(position[0]) + 1, int(position[1]))

def convertCoordinatesToPosition(coordinates):
	x, y = coordinates
	return XCOORDINATES[x - 1] + str(y)

class Game(models.Model):
	status = models.IntegerField(default = 0)

	def isPending(self):
		return self.status == GAMESTATUS["PENDING"]

	def isActive(self):
		return self.status == GAMESTATUS["ACTIVE"]

	def isFinished(self):
		return self.status == GAMESTATUS["FINISHED"]

	def getGameUserCurrentTurn(self):
		history = loadHistoryByGame(self)
		gameUsers = loadGameUsersByGame(self)

		if len(history):
			if gameUsers[0] == history[-1].gameUser:
				return gameUsers[1]
			return gameUsers[0]

		if gameUsers[0].isWhite():
			return gameUsers[0]
		return gameUsers[1]

	def addUser(self, user):
		gameUsers = self.gameuser_set.all()

		if len(gameUsers) >= 2:
			return

		for gameUser in gameUsers:
			if gameUser.user.id == user.id:
				return

		color = COLOR["WHITE"]
		if len(gameUsers) == 1 and gameUsers[0].color == COLOR["WHITE"]:
			color = COLOR["BLACK"]
		return newGameUser(game = self, user = user, color = color)

	def startGame(self):
		if self.isPending() and self.gameuser_set.count() == 2:
			self.status = GAMESTATUS["ACTIVE"]
			self.save()
			self._createInitialPieces()
			return True
		return False

	def _createInitialPieces(self):
		for gameUser in self.gameuser_set.all():
			if gameUser.isWhite():
				for data in [
					("A1", "ROOK"), ("B1", "KNIGHT"), ("C1", "BISHOP"), ("D1", "QUEEN"),
					("E1", "KING"), ("F1", "BISHOP"), ("G1", "KNIGHT"), ("H1", "ROOK"),
					("A2", "PAWN"), ("B2", "PAWN"), ("C2", "PAWN"), ("D2", "PAWN"),
					("E2", "PAWN"), ("F2", "PAWN"), ("G2", "PAWN"), ("H2", "PAWN")
				]:
					position, type = data
					newPiece(gameUser = gameUser, position = position, type = type)
			else:
				for data in [
					("A8", "ROOK"), ("B8", "KNIGHT"), ("C8", "BISHOP"), ("D8", "QUEEN"),
					("E8", "KING"), ("F8", "BISHOP"), ("G8", "KNIGHT"), ("H8", "ROOK"),
					("A7", "PAWN"), ("B7", "PAWN"), ("C7", "PAWN"), ("D7", "PAWN"),
					("E7", "PAWN"), ("F7", "PAWN"), ("G7", "PAWN"), ("H7", "PAWN")
				]:
					position, type = data
					newPiece(gameUser = gameUser, position = position, type = type)

	def getAvailableMoves(self):
		result = []
		if self.isActive():
			for piece in loadPiecesByGameUser(self.getGameUserCurrentTurn()):
				positions = piece.getLegalMovePositions()
				result.append({"piece": piece, "positions": positions})
		return result

class GameUser(models.Model):
	game = models.ForeignKey(Game)
	user = models.ForeignKey(User)
	color = models.IntegerField()

	def isBlack(self):
		return self.color == COLOR["BLACK"]

	def isWhite(self):
		return self.color == COLOR["WHITE"]

class Piece(models.Model):
	gameUser = models.ForeignKey(GameUser)
	position = models.CharField(max_length = 2)
	type = models.IntegerField()

	def setPosition(self, toPosition):
		fromPosition = self.position
		self.position = toPosition
		self.save()
		newHistory(piece = self, fromPosition = fromPosition, toPosition = toPosition)

	def isWhite(self):
		return self.gameUser.isWhite()

	def isBlack(self):
		return self.gameUser.isBlack()

	def hasMoved(self):
		return getHistoryCountByPiece(self) > 0

class Pawn(Piece):

	def getLegalMovePositions(self):
		offsetYModifier = 1
		if self.isBlack():
			offsetYModifier = -1
		returnValue = [getPositionByOffset(self.position, 0, 1 * offsetYModifier)]
		if self.hasMoved() == False:
			returnValue.append(getPositionByOffset(self.position, 0, 2 * offsetYModifier))
		return [x for x in returnValue if x != ""]

	class Meta:
		proxy = True

class Rook(Piece):

	def getLegalMovePositions(self):
		returnValue = []
		for i in range(1, 7):
			for coordinates in [(i, 0), (i * -1, 0), (0, i), (0, i * -1)]:
				x, y = coordinates
				returnValue.append(getPositionByOffset(self.position, x, y))
		return [x for x in returnValue if x != ""]

	class Meta:
		proxy = True

class Knight(Piece):

	def getLegalMovePositions(self):
		returnValue = []
		for coordinates in [(2, 1), (-2, 1), (-2, -1), (2, -1), (1, 2), (-1, 2), (-1, -2), (1, -2)]:
			x, y = coordinates
			returnValue.append(getPositionByOffset(self.position, x, y))
		return [x for x in returnValue if x != ""]

	class Meta:
		proxy = True

class Bishop(Piece):

	def getLegalMovePositions(self):
		returnValue = []
		for i in range(1, 7):
			for coordinates in [(i, i), (-i, i), (-i, -i), (i, -i)]:
				x, y = coordinates
				returnValue.append(getPositionByOffset(self.position, x, y))
		return [x for x in returnValue if x != ""]

	class Meta:
		proxy = True

class Queen(Piece):

	def getLegalMovePositions(self):
		returnValue = []
		for i in range(1, 7):
			for coordinates in [(i, i), (-i, i), (-i, -i), (i, -i), (i, 0), (-i, 0), (0, i), (0, -i)]:
				x, y = coordinates
				returnValue.append(getPositionByOffset(self.position, x, y))
		return [x for x in returnValue if x != ""]

	class Meta:
		proxy = True

class King(Piece):

	def getLegalMovePositions(self):
		returnValue = []
		for coordinates in [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
			x, y = coordinates
			returnValue.append(getPositionByOffset(self.position, x, y))
		return [x for x in returnValue if x != ""]

	class Meta:
		proxy = True

class History(models.Model):
	piece = models.ForeignKey(Piece)
	fromPosition = models.CharField(max_length = 2)
	toPosition = models.CharField(max_length = 2)
	datetimeCreated = models.DateTimeField(auto_now_add = True)
