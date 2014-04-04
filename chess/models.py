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

#TODO: when calling any 'new' function, delete any preloaded data on associated objects
def new_game():
	return Game.objects.create(status = GAMESTATUS["PENDING"])

def new_user(username):
	return User.objects.create(username = username)

def new_game_user(game, user, color):
	return GameUser.objects.create(game = game, user = user, color = color)

def new_piece(gameUser, position, type):
	return Piece.objects.create(gameUser = gameUser, position = position, type = PIECETYPE[type])

def new_history(piece, fromPosition, toPosition):
	return History.objects.create(piece = piece, fromPosition = fromPosition, toPosition = toPosition)

def load_game_by_id(id):
	return Game.objects.get(id = id)

def load_pending_games():
	return Game.objects.filter(status = GAMESTATUS['PENDING']).order_by("-id")

def load_active_games_by_user_id(userID):
	return Game.objects.filter(status = GAMESTATUS['ACTIVE'], gameuser__user_id = userID).order_by("-id")

def load_game_users_by_game(game):
	return GameUser.objects.filter(game = game)

def load_game_users_by_game_modified_since(game, datetime):
	return GameUser.objects.filter(game = game, datetimeLastModified__gte = datetime)

def load_pieces_by_game(game):
	return Piece.objects.filter(gameUser__game = game).prefetch_related("gameUser").order_by("-id")

def load_pieces_by_game_modified_since(game, datetime):
	return Piece.objects.filter(gameUser__game = game, datetimeLastModified__gte = datetime).prefetch_related("gameUser")

def load_pieces_by_game_user(gameUser):
	return Piece.objects.filter(gameUser = gameUser)

def load_history_by_game(game):
	return History.objects.filter(piece__gameUser__game = game).order_by("id")

def load_history_by_game_modified_since(game, datetime):
	return History.objects.filter(piece__gameUser__game = game, datetimeLastModified__gte = datetime)

def loadHistoryByPiece(piece):
	return History.objects.filter(piece = piece)

def get_position_by_offset(startingPosition, offsetX, offsetY):
	x, y = convert_position_to_coordinates(startingPosition)
	if 1 <= x + offsetX <= 8 and 1 <= y + offsetY <= 8:
		return convert_coordinates_to_position((x + offsetX, y + offsetY))
	return ""

def convert_position_to_coordinates(position):
	if len(position) != 2 or position[0] not in "ABCDEFGH" or position[1] not in "12345678":
		return (0, 0)
	return (XCOORDINATES.index(position[0]) + 1, int(position[1]))

def convert_coordinates_to_position(coordinates):
	x, y = coordinates
	return XCOORDINATES[x - 1] + str(y)

class Game(models.Model):
	status = models.IntegerField(default = 0)
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def is_pending(self):
		return self.status == GAMESTATUS["PENDING"]

	def is_active(self):
		return self.status == GAMESTATUS["ACTIVE"]

	def is_finished(self):
		return self.status == GAMESTATUS["FINISHED"]

	def clone(self): # don't ever save a clone
		clone = Game(id = self.id)
		clone.pieces = self.getPieces()
		clone.gameUsers = self.getGameUsers()
		clone.history = self.getHistory()
		return clone

	def getPieces(self):
		if hasattr(self, "pieces") == False:
			self.pieces = load_pieces_by_game(self)
		return self.pieces

	def getPiecesModifiedSince(self, datetime):
		return load_pieces_by_game_modified_since(self, datetime)

	def getGameUsers(self):
		if hasattr(self, "gameUsers") == False:
			self.gameUsers = load_game_users_by_game(self)
		return self.gameUsers

	def getGameUsersModifiedSince(self, datetime):
		return load_game_users_by_game_modified_since(self, datetime)

	def getPieceByID(self, piece_id):
		for piece in self.getPieces():
			if piece.id == piece_id:
				return piece
		return None

	def getHistory(self):
		if hasattr(self, "history") == False:
			self.history = load_history_by_game(self)
		return self.history

	def getHistoryModifiedSince(self, datetime):
		return load_history_by_game_modified_since(self, datetime)

	def getGameUserCurrentTurn(self):
		history = self.getHistory()
		gameUsers = self.getGameUsers()

		if len(history):
			if gameUsers[0] == history[history.count() - 1].piece.gameUser:
				return gameUsers[1]
			return gameUsers[0]

		if gameUsers[0].is_white():
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
		gameUser = new_game_user(game = self, user = user, color = color)
		self.startGame()
		return gameUser

	def startGame(self):
		if self.is_pending() and self.gameuser_set.count() == 2:
			self.status = GAMESTATUS["ACTIVE"]
			self.save()
			self._createInitialPieces()
			return True
		return False

	def _createInitialPieces(self):
		for gameUser in self.gameuser_set.all():
			if gameUser.is_white():
				for data in [
					("A1", "ROOK"), ("B1", "KNIGHT"), ("C1", "BISHOP"), ("D1", "QUEEN"),
					("E1", "KING"), ("F1", "BISHOP"), ("G1", "KNIGHT"), ("H1", "ROOK"),
					("A2", "PAWN"), ("B2", "PAWN"), ("C2", "PAWN"), ("D2", "PAWN"),
					("E2", "PAWN"), ("F2", "PAWN"), ("G2", "PAWN"), ("H2", "PAWN")
				]:
					position, type = data
					new_piece(gameUser = gameUser, position = position, type = type)
			else:
				for data in [
					("A8", "ROOK"), ("B8", "KNIGHT"), ("C8", "BISHOP"), ("D8", "QUEEN"),
					("E8", "KING"), ("F8", "BISHOP"), ("G8", "KNIGHT"), ("H8", "ROOK"),
					("A7", "PAWN"), ("B7", "PAWN"), ("C7", "PAWN"), ("D7", "PAWN"),
					("E7", "PAWN"), ("F7", "PAWN"), ("G7", "PAWN"), ("H7", "PAWN")
				]:
					position, type = data
					new_piece(gameUser = gameUser, position = position, type = type)

	def getAvailableMoves(self):
		possibleMoves = []
		if self.is_active():
			gameUser = self.getGameUserCurrentTurn()
			possibleMoves = self.getPossibleMoves()
			possibleMoves = self.filterMovesThatLeavesPlayerOutOfCheck(possibleMoves, gameUser)
			possibleMoves = self.filterMovesForGameUser(possibleMoves, gameUser)
		return possibleMoves

	def gameuser_is_in_check(self, gameUser):
		king = self.getKingForGameUser(gameUser)
		for move in self.getPossibleMovesForGameUser(self.getOtherGameUser(gameUser)):
			for position in move['positions']:
				if position == king.position:
					return True
		return False

	def getKingForGameUser(self, gameUser):
		for piece in self.getPieces():
			if piece.isKing() and piece.gameUser == gameUser:
				return piece

	def filterMovesForGameUser(self, moves, gameUser):
		result = []
		for move in moves:
			if move['piece'].gameUser == gameUser:
				result.append(move)
		return result

	def filterMovesThatLeavesPlayerOutOfCheck(self, moves, gameUser):
		result = []
		for move in moves:
			positions = []
			for position in move['positions']:
				if self.playerIsInCheckAfterMovingPieceToPosition(move['piece'], position) == False:
					positions.append(position)
			if len(positions):
				result.append({'piece': move['piece'], 'positions': positions})
		return result

	def playerIsInCheckAfterMovingPieceToPosition(self, piece, position):
		result = False
		originalPosition = piece.position
		cloneGame = self.clone()
		pieceAtPosition = self.get_piece_at_position(position)

		if pieceAtPosition:
			pieceAtPosition.position = ""
		piece.position = position
		piece.mockMove = True

		if cloneGame.gameuser_is_in_check(piece.gameUser):
			result = True

		piece.position = originalPosition
		del piece.mockMove
		if pieceAtPosition:
			pieceAtPosition.position = position

		return result

	def getPossibleMoves(self):
		if hasattr(self, "possibleMoves") == False:
			self.possibleMoves = self._calculatePossibleMoves()
		return self.possibleMoves

	def _calculatePossibleMoves(self):
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
			result = self.getAvailableMovesForPiece_king(piece)
		return [position for position in result if position != '']

	def getAvailableMovesForPiece_pawn(self, piece):
		result = []

		y_direction = 1
		if piece.is_black():
			y_direction = -1

		position = get_position_by_offset(piece.position, 0, y_direction)
		if self.get_piece_at_position(position) == None:
			result.append(position)
			if piece.hasMoved() == False:
				position = get_position_by_offset(piece.position, 0, y_direction + y_direction)
				if self.get_piece_at_position(position) == None:
					result.append(position)

		#capturing
		position = get_position_by_offset(piece.position, 1, y_direction)
		if self.positionIsOccupiedByOtherColor(position, piece):
			result.append(position)
		position = get_position_by_offset(piece.position, -1, y_direction)
		if self.positionIsOccupiedByOtherColor(position, piece):
			result.append(position)

		return result

	def getAvailableMovesForPiece_knight(self, piece):
		result = []
		for coordinates in [(2, 1), (-2, 1), (-2, -1), (2, -1), (1, 2), (-1, 2), (-1, -2), (1, -2)]:
			x, y = coordinates
			position = get_position_by_offset(piece.position, x, y)
			if self.positionIsOccupiedBySameColor(position, piece) == False:
				result.append(position)
		return result

	def getAvailableMovesForPiece_cardinal(self, piece, distance):
		result = []
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, 0, i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, 0, -i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, i, 0)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, -i, 0)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		return result

	def getAvailableMovesForPiece_diagonal(self, piece, distance):
		result = []
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, i, i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, i, -i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, -i, -i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		for i in range(1, distance + 1):
			position = get_position_by_offset(piece.position, -i, i)
			if self._appendPositionAndDetermineIfShouldContinue(position, piece, result) == False:
				break
		return result

	def getAvailableMovesForPiece_king(self, piece):
		result = self.getAvailableMovesForPiece_cardinal(piece, 1)
		result += self.getAvailableMovesForPiece_diagonal(piece, 1)

		if piece.hasMoved() == False and piece.gameUser.has_been_in_check() == False:
			y = '1'
			if piece.is_black():
				y = '8'
			if (
				self.get_piece_at_position('F' + y) == None
				and self.get_piece_at_position('G' + y) == None
				and self.get_piece_at_position('H' + y)
				and self.get_piece_at_position('H' + y).hasMoved() == False
				and self.playerIsInCheckAfterMovingPieceToPosition(piece, 'F' + y) == False
				and self.playerIsInCheckAfterMovingPieceToPosition(piece, 'G' + y) == False
			):
				result += ['G' + y]
			if (
				self.get_piece_at_position('D' + y) == None
				and self.get_piece_at_position('C' + y) == None
				and self.get_piece_at_position('B' + y) == None
				and self.get_piece_at_position('A' + y)
				and self.get_piece_at_position('A' + y).hasMoved() == False
				and self.playerIsInCheckAfterMovingPieceToPosition(piece, 'D' + y) == False
				and self.playerIsInCheckAfterMovingPieceToPosition(piece, 'C' + y) == False
			):
				result += ['C' + y]

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
		pieceAtPosition = self.get_piece_at_position(position)
		if pieceAtPosition and (pieceAtPosition.gameUser.color == piece.gameUser.color):
			return True
		return False

	def positionIsOccupiedByOtherColor(self, position, piece):
		pieceAtPosition = self.get_piece_at_position(position)
		if pieceAtPosition and (pieceAtPosition.gameUser.color != piece.gameUser.color):
			return True
		return False

	def get_piece_at_position(self, position):
		for piece in self.getPieces():
			if piece.position == position:
				return piece
		return None

	def move_piece_to_position(self, piece_id, position):
		piece = self.getPieceByID(piece_id)
		if self._can_piece_move_to_position(piece, position):
			pieceAtPosition = self.get_piece_at_position(position)
			if pieceAtPosition:
				pieceAtPosition.moveToPosition("")
			piece.moveToPosition(position)

			#TODO: maybe these should be methods instead of deleting the properties directly? or the latest history could be appended to the history property
			del self.history
			del self.possibleMoves

			otherGameUser = self.getOtherGameUser(piece.gameUser)
			if self.gameuser_is_in_check(otherGameUser):
				otherGameUser.hasBeenInCheck = True
				otherGameUser.save()

	def _can_piece_move_to_position(self, piece, position):
		for move in self.getAvailableMoves():
			if move['piece'] == piece and position in move['positions']:
				return True
		return False

class GameUser(models.Model):
	game = models.ForeignKey(Game)
	user = models.ForeignKey(User)
	color = models.IntegerField()
	hasBeenInCheck = models.BooleanField(default = False)
	datetimeLastModified = models.DateTimeField(auto_now = True)

	def get_color(self):
		for key, value in COLOR.items():
			if value == self.color:
				return key

	def is_black(self):
		return self.color == COLOR["BLACK"]

	def is_white(self):
		return self.color == COLOR["WHITE"]

	def getPieces(self):
		if hasattr(self, "pieces") == False:
			self.pieces = load_pieces_by_game_user(self)
		return self.pieces

	def has_been_in_check(self):
		return bool(self.hasBeenInCheck)

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

		x, y = convert_position_to_coordinates(self.position)
		if self.isPawn() and ((self.is_white() and y == 8) or (self.is_black() and y == 1)):
			self.type = PIECETYPE["QUEEN"]

		self.save()
		new_history(piece = self, fromPosition = fromPosition, toPosition = toPosition)

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

	def is_white(self):
		return self.gameUser.is_white()

	def is_black(self):
		return self.gameUser.is_black()

	def getHistory(self):
		if hasattr(self, "history") == False:
			self.history = loadHistoryByPiece(self)
		return self.history

	def hasMoved(self):
		if hasattr(self, "mockMove"):
			return True
		return len(self.getHistory()) > 0

class History(models.Model):
	piece = models.ForeignKey(Piece)
	fromPosition = models.CharField(max_length = 2)
	toPosition = models.CharField(max_length = 2)
	datetimeLastModified = models.DateTimeField(auto_now = True)
