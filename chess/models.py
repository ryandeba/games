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
	return Piece.objects.filter(gameUser__game = game)

def loadPiecesByGameUser(gameUser):
	return Piece.objects.filter(gameUser = gameUser)

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

	def getPieces(self):
		if hasattr(self, "pieces") == False:
			self.pieces = loadPiecesByGame(self)
		return self.pieces

	def getGameUserCurrentTurn(self):
		history = loadHistoryByGame(self)
		gameUsers = loadGameUsersByGame(self)

		if len(history):
			if gameUsers[0] == history[history.count() - 1].piece.gameUser:
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
		#TODO: check if the user is in check, only allow moves that get the person out of check
		result = []
		if self.isActive():
			for piece in loadPiecesByGameUser(self.getGameUserCurrentTurn()):
				positions = self.getAvailableMovesForPiece(piece)
				if len(positions):
					result.append({"piece": piece, "positions": positions})
		return result

	def getAvailableMovesForPiece(self, piece):
		result = []
		if piece.isPawn():
			result = self.getAvailableMovesForPiece_pawn(piece)
		if piece.isRook():
			result = self.getAvailableMovesForPiece_cardinal(piece, 8)
		if piece.isKnight():
			result = self.getAvailableMovesForPiece_knight(piece)
		if piece.isBishop():
			result = self.getAvailableMovesForPiece_diagonal(piece, 8)
		if piece.isQueen():
			result = self.getAvailableMovesForPiece_cardinal(piece, 8) + self.getAvailableMovesForPiece_diagonal(piece, 8)
		if piece.isKing():
			result = self.getAvailableMovesForPiece_cardinal(piece, 1) + self.getAvailableMovesForPiece_diagonal(piece, 1)
			#TODO: add castling
		return [position for position in result if position != '']

	def getAvailableMovesForPiece_pawn(self, piece):
		#TODO: add capture positions
		result = []
		if piece.isWhite():
			position = getPositionByOffset(piece.position, 0, 1)
		else:
			position = getPositionByOffset(piece.position, 0, -1)
		if self.getPieceAtPosition(position) == None:
			result.append(position)

		if piece.hasMoved() == False:
			if piece.isWhite():
				position = getPositionByOffset(piece.position, 0, 2)
			else:
				position = getPositionByOffset(piece.position, 0, -2)
			if self.getPieceAtPosition(position) == None:
				result.append(position)
		return result

	def getAvailableMovesForPiece_knight(self, piece):
		result = []
		for coordinates in [(2, 1), (-2, 1), (-2, -1), (2, -1), (1, 2), (-1, 2), (-1, -2), (1, -2)]:
			x, y = coordinates
			position = getPositionByOffset(piece.position, x, y)
			if self.getPieceAtPosition(position) == None:
				result.append(position)
		return result

	def getAvailableMovesForPiece_cardinal(self, piece, distance):
		result = []
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, 0, i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, 0, -i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, i, 0)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, -i, 0)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		return result

	def getAvailableMovesForPiece_diagonal(self, piece, distance):
		result = []
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, i, i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, i, -i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, -i, -i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = getPositionByOffset(piece.position, -i, i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		return result

	#TODO: please rename this or split it up. how embarassing
	def _appendPositionAndDetermineIfShouldContinue(self, position, piece, result):
		if self.positionIsOccupiedBySameColor(position, piece):
			return False
		if self.positionIsOccupiedByOtherColor(position, piece):
			result.append(position)
			return False
		result.append(position)
		return True

	def positionIsOccupiedBySameColor(self, position, piece):
		pieceAtPosition = self.getPieceAtPosition(position)
		if pieceAtPosition and (pieceAtPosition.gameUser.color == piece.gameUser.color):
			return True
		return False

	def positionIsOccupiedByOtherColor(self, position, piece):
		pieceAtPosition = self.getPieceAtPosition(position)
		if pieceAtPosition and (pieceAtPosition.gameUser.color != piece.gameUser.color):
			return True
		return False

	def getPieceAtPosition(self, position):
		for piece in self.getPieces():
			if piece.position == position:
				return piece
		return None

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

	def moveToPosition(self, toPosition):
		fromPosition = self.position
		self.position = toPosition
		self.save()
		newHistory(piece = self, fromPosition = fromPosition, toPosition = toPosition)

	def isPawn(self):
		return self.type == PIECETYPE["PAWN"]

	def isRook(self):
		return self.type == PIECETYPE["ROOK"]

	def isKnight(self):
		return self.type == PIECETYPE["KNIGHT"]

	def isBishop(self):
		return self.type == PIECETYPE["BISHOP"]

	def isQueen(self):
		return self.type == PIECETYPE["QUEEN"]

	def isKing(self):
		return self.type == PIECETYPE["KING"]

	def isWhite(self):
		return self.gameUser.isWhite()

	def isBlack(self):
		return self.gameUser.isBlack()

	def hasMoved(self):
		return getHistoryCountByPiece(self) > 0

class History(models.Model):
	piece = models.ForeignKey(Piece)
	fromPosition = models.CharField(max_length = 2)
	toPosition = models.CharField(max_length = 2)
	datetimeCreated = models.DateTimeField(auto_now_add = True)