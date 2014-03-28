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

def loadPendingGames():
	return Game.objects.filter(status = GAMESTATUS['PENDING']).order_by("-id")

def loadActiveGamesByUserID(userID):
	return Game.objects.filter(status = GAMESTATUS['ACTIVE'], gameuser__user_id = userID).order_by("-id")

def loadGameUsersByGame(game):
	return GameUser.objects.filter(game = game)

def loadGameUsersByGameModifiedSince(game, datetime):
	return GameUser.objects.filter(game = game, datetimeLastModified__gte = datetime)

def loadPiecesByGame(game):
	return Piece.objects.filter(gameUser__game = game)

def loadPiecesByGameModifiedSince(game, datetime):
	return Piece.objects.filter(gameUser__game = game, datetimeLastModified__gte = datetime)

def loadPiecesByGameUser(gameUser):
	return Piece.objects.filter(gameUser = gameUser)

def loadHistoryByGame(game):
	return History.objects.filter(piece__gameUser__game = game).order_by("id")

def loadHistoryByPiece(piece):
	return History.objects.filter(piece = piece)

def loadHistoryCountByPiece(piece):
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
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def isPending(self):
		return self.status == GAMESTATUS["PENDING"]

	def isActive(self):
		return self.status == GAMESTATUS["ACTIVE"]

	def isFinished(self):
		return self.status == GAMESTATUS["FINISHED"]

	def clone(self): # don't ever save a clone
		clone = Game(id = self.id)
		return clone

	def getPieces(self):
		if hasattr(self, "pieces") == False:
			self.pieces = loadPiecesByGame(self)
		return self.pieces

	def getPiecesModifiedSince(self, datetime):
		return loadPiecesByGameModifiedSince(self, datetime)

	def getGameUsers(self):
		if hasattr(self, "gameUsers") == False:
			self.gameUsers = loadGameUsersByGame(self)
		return self.gameUsers

	def getGameUsersModifiedSince(self, datetime):
		return loadGameUsersByGameModifiedSince(self, datetime)

	def getPieceByID(self, piece_id):
		for piece in self.getPieces():
			if piece.id == piece_id:
				return piece
		return None

	def getHistory(self):
		if hasattr(self, "history") == False:
			self.history = loadHistoryByGame(self)
		return self.history

	def getGameUserCurrentTurn(self):
		history = self.getHistory()
		gameUsers = self.getGameUsers()

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
			if gameUser.user == user:
				return

		color = COLOR["WHITE"]
		if len(gameUsers) == 1 and gameUsers[0].color == COLOR["WHITE"]:
			color = COLOR["BLACK"]
		gameUser = newGameUser(game = self, user = user, color = color)
		self.startGame()
		return gameUser

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
		possibleMoves = []
		if self.isActive():
			gameUser = self.getGameUserCurrentTurn()
			possibleMoves = self.getPossibleMoves()
			possibleMoves = self.filterMovesThatLeavesPlayerOutOfCheck(possibleMoves, gameUser)
			possibleMoves = self.filterMovesForGameUser(possibleMoves, gameUser)
		return possibleMoves

	def gameUserIsInCheck(self, gameUser):
		king = gameUser.getPieceOfType(PIECETYPE['KING'])
		for move in self.getPossibleMovesForGameUser(self.getOtherGameUser(gameUser)):
			for position in move['positions']:
				if position == king.position:
					return True
		return False

	def filterMovesForGameUser(self, moves, gameUser):
		result = []
		for move in moves:
			if move['piece'].gameUser == gameUser:
				result.append(move)
		return result

	def filterMovesThatLeavesPlayerOutOfCheck(self, moves, gameUser):
		result = []
		for move in moves:
			for position in move['positions']:
				if self.playerIsInCheckAfterMovingPieceToPosition(move['piece'], position) == False:
					result.append(move)
		return result

	def playerIsInCheckAfterMovingPieceToPosition(self, piece, position):
		result = False
		originalPosition = piece.position
		cloneGame = self.clone()
		piece.position = position
		if cloneGame.gameUserIsInCheck(piece.gameUser):
			result = True
		piece.position = originalPosition
		return result

	def getPossibleMoves(self):
		if hasattr(self, "possibleMoves") == False:
			self.possibleMoves = self.calculatePossibleMoves()
		return self.possibleMoves

	def calculatePossibleMoves(self):
		possibleMoves = []
		for piece in self.getPieces():
			positions = self.getAvailableMovesForPiece(piece)
			if len(positions):
				possibleMoves.append({"piece": piece, "positions": positions})
		return possibleMoves

	def getPossibleMovesForGameUser(self, gameUser):
		result = []
		moves = self.getPossibleMoves()
		for move in moves:
			if move['piece'].gameUser == gameUser:
				result.append(move)
		return result

	def getOtherGameUser(self, gameUser):
		for thisGameUser in self.getGameUsers():
			if thisGameUser != gameUser:
				return thisGameUser
		return None

	def getAvailableMovesForPiece(self, piece):
		result = []
		if piece.position == "":
			result = []
		elif piece.isPawn():
			result = self.getAvailableMovesForPiece_pawn(piece)
		elif piece.isRook():
			result = self.getAvailableMovesForPiece_cardinal(piece, 8)
		elif piece.isKnight():
			result = self.getAvailableMovesForPiece_knight(piece)
		elif piece.isBishop():
			result = self.getAvailableMovesForPiece_diagonal(piece, 8)
		elif piece.isQueen():
			result = self.getAvailableMovesForPiece_cardinal(piece, 8) + self.getAvailableMovesForPiece_diagonal(piece, 8)
		elif piece.isKing():
			result = self.getAvailableMovesForPiece_cardinal(piece, 1) + self.getAvailableMovesForPiece_diagonal(piece, 1)
			#TODO: add castling
		return [position for position in result if position != '']

	def getAvailableMovesForPiece_pawn(self, piece):
		result = []
		y_direction = 1
		if piece.isBlack():
			y_direction = -1
		position = getPositionByOffset(piece.position, 0, y_direction)
		if self.getPieceAtPosition(position) == None:
			result.append(position)

		position = getPositionByOffset(piece.position, 1, y_direction)
		if self.positionIsOccupiedByOtherColor(position, piece):
			result.append(position)
		position = getPositionByOffset(piece.position, -1, y_direction)
		if self.positionIsOccupiedByOtherColor(position, piece):
			result.append(position)

		if piece.hasMoved() == False:
			position = getPositionByOffset(piece.position, 0, y_direction + y_direction)
			if self.getPieceAtPosition(position) == None:
				result.append(position)
		return result

	def getAvailableMovesForPiece_knight(self, piece):
		result = []
		for coordinates in [(2, 1), (-2, 1), (-2, -1), (2, -1), (1, 2), (-1, 2), (-1, -2), (1, -2)]:
			x, y = coordinates
			position = getPositionByOffset(piece.position, x, y)
			if self.positionIsOccupiedBySameColor(position, piece) == False:
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

	def movePieceToPosition(self, piece_id, position):
		piece = self.getPieceByID(piece_id)
		pieceAtPosition = self.getPieceAtPosition(position)
		if self.canPieceMoveToPosition(piece, position):
			if pieceAtPosition:
				pieceAtPosition.moveToPosition("")
			piece.moveToPosition(position)

	def canPieceMoveToPosition(self, piece, position):
		for move in self.getAvailableMoves():
			if move['piece'] == piece and position in move['positions']:
				return True
		return False

class GameUser(models.Model):
	game = models.ForeignKey(Game)
	user = models.ForeignKey(User)
	color = models.IntegerField()
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def getColor(self):
		for key, value in COLOR.items():
			if value == self.color:
				return key

	def isBlack(self):
		return self.color == COLOR["BLACK"]

	def isWhite(self):
		return self.color == COLOR["WHITE"]

	def getPieces(self):
		if hasattr(self, "pieces") == False:
			self.pieces = loadPiecesByGameUser(self)
		return self.pieces

	def getPieceOfType(self, pieceType):
		for piece in self.getPieces():
			if piece.type == pieceType:
				return piece
		return None

class Piece(models.Model):
	gameUser = models.ForeignKey(GameUser)
	position = models.CharField(max_length = 2)
	type = models.IntegerField()
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def __unicode__(self):
		return self.getPieceType()

	def moveToPosition(self, toPosition):
		fromPosition = self.position
		self.position = toPosition
		self.save()
		newHistory(piece = self, fromPosition = fromPosition, toPosition = toPosition)

	def getPieceType(self):
		for key, value in PIECETYPE.items():
			if value == self.type:
				return key

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
		return loadHistoryCountByPiece(self) > 0

class History(models.Model):
	piece = models.ForeignKey(Piece)
	fromPosition = models.CharField(max_length = 2)
	toPosition = models.CharField(max_length = 2)
	datetimeLastModified = models.DateTimeField(auto_now = True)
