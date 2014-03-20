from django.test import TestCase

from chess.models import *

def setupGame():
	game = newGame()
	user1 = newUser(username = "1")
	user2 = newUser(username = "2")
	gameUser1 = game.addUser(user1)
	gameUser2 = game.addUser(user2)
	game.startGame()
	return (game, user1, user2, gameUser1, gameUser2)

class UtilityTests(TestCase):

	def test_newGame(self):
		game = newGame()
		self.assertEqual(game, Game.objects.get(id = game.id))

	def test_loadGameByID(self):
		game = newGame()
		loadedGame = loadGameByID(game.id)
		self.assertEqual(game, loadedGame)

	def test_loadPiecesByGame(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		self.assertEqual(32, len(loadPiecesByGame(game)))

	def test_convertPositionToCoordinates(self):
		self.assertEqual((1, 1), convertPositionToCoordinates("A1"))
		self.assertEqual((2, 2), convertPositionToCoordinates("B2"))
		self.assertEqual((3, 3), convertPositionToCoordinates("C3"))

	def test_convertCoordinatesToPosition(self):
		self.assertEqual("A1", convertCoordinatesToPosition((1, 1)))
		self.assertEqual("B2", convertCoordinatesToPosition((2, 2)))
		self.assertEqual("C3", convertCoordinatesToPosition((3, 3)))

	def test_getPositionByOffset(self):
		self.assertEqual("A1", getPositionByOffset("A1", 0, 0))
		self.assertEqual("B2", getPositionByOffset("A1", 1, 1))
		self.assertEqual("A1", getPositionByOffset("B2", -1, -1))
		self.assertEqual("", getPositionByOffset("A1", -1, -1))
		self.assertEqual("", getPositionByOffset("H8", 1, 1))

class GameTests(TestCase):

	def test_addUserToGame(self):
		game = Game.objects.create()
		user1 = User.objects.create(username = "1")
		user2 = User.objects.create(username = "2")
		user3 = User.objects.create(username = "3")

		gameUser1 = game.addUser(user1)
		gameUserNone = game.addUser(user1)
		gameUser2 = game.addUser(user2)
		gameUser3 = game.addUser(user3)

		self.assertEqual(False, gameUser1.isBlack())
		self.assertEqual(None, gameUserNone)
		self.assertEqual(True, gameUser2.isBlack())
		self.assertEqual(None, gameUser3)

	def test_startGame(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		self.assertEqual(True, game.isActive())

	def test_startGame_statusIsNotChangedIfStatusIsNotPending(self):
		game = newGame()
		game.status = GAMESTATUS["FINISHED"]
		user1 = User.objects.create(username = "1")
		user2 = User.objects.create(username = "2")

		game.addUser(user1)
		game.addUser(user2)

		game.startGame()

		self.assertEqual(False, game.isActive())

	def test_startGame_statusIsNotChangedIfThereAreNotTwoPlayers(self):
		game = newGame()
		game.startGame()
		self.assertEqual(False, game.isActive())

	def test_getGameUserCurrentTurn_returnsWhiteUserIfThereIsNoHistory(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		self.assertEqual(True, game.getGameUserCurrentTurn().isWhite())

	def test_getAvailableMoves(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		expectedResult = []
		actualResult = game.getAvailableMoves()

		self.assertEqual(expectedResult, actualResult)

class PawnTests(TestCase):
	
	def test_getLegalMovePositions(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		whitePawn = Pawn(gameUser = gameUser1, position = "A2", type = PIECETYPE["PAWN"])
		blackPawn = Pawn(gameUser = gameUser2, position = "A7", type = PIECETYPE["PAWN"])

		self.assertEqual(["A3", "A4"], whitePawn.getLegalMovePositions())
		self.assertEqual(["A6", "A5"], blackPawn.getLegalMovePositions())

class RookTests(TestCase):
	
	def test_getLegalMovePositions(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()
		rook = Rook(gameUser = gameUser1, position = "D4", type = PIECETYPE["ROOK"])

		expectedResult = ["D1", "D2", "D3", "D5", "D6", "D7", "D8", "A4", "B4", "C4", "E4", "F4", "G4", "H4"]
		expectedResult.sort()
		actualResult = rook.getLegalMovePositions()
		actualResult.sort()

		self.assertEqual(expectedResult, actualResult)

class KnightTests(TestCase):
	
	def test_getLegalMovePositions(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()
		knight = Knight(gameUser = gameUser1, position = "D4", type = PIECETYPE["KNIGHT"])

		expectedResult = ["E6", "E2", "F3", "F5", "C6", "C2", "B3", "B5"]
		expectedResult.sort()
		actualResult = knight.getLegalMovePositions()
		actualResult.sort()

		self.assertEqual(expectedResult, actualResult)

class BishopTests(TestCase):
	
	def test_getLegalMovePositions(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()
		bishop = Bishop(gameUser = gameUser1, position = "D4", type = PIECETYPE["BISHOP"])

		expectedResult = ["E5", "F6", "G7", "H8", "E3", "F2", "G1", "C5", "B6", "A7", "C3", "B2", "A1"]
		expectedResult.sort()
		actualResult = bishop.getLegalMovePositions()
		actualResult.sort()

		self.assertEqual(expectedResult, actualResult)

class QueenTests(TestCase):
	
	def test_getLegalMovePositions(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()
		queen = Queen(gameUser = gameUser1, position = "D4", type = PIECETYPE["QUEEN"])

		expectedResult = [
			"D1", "D2", "D3", "D5", "D6", "D7", "D8", "A4", "B4", "C4", "E4", "F4", "G4", "H4",
			"E5", "F6", "G7", "H8", "E3", "F2", "G1", "C5", "B6", "A7", "C3", "B2", "A1"
		]
		expectedResult.sort()
		actualResult = queen.getLegalMovePositions()
		actualResult.sort()

		self.assertEqual(expectedResult, actualResult)

class KingTests(TestCase):
	
	def test_getLegalMovePositions(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()
		king = King(gameUser = gameUser1, position = "D4", type = PIECETYPE["KING"])

		expectedResult = ["D5", "E3", "E4", "E5", "D3", "C3", "C4", "C5"]
		expectedResult.sort()
		actualResult = king.getLegalMovePositions()
		actualResult.sort()

		self.assertEqual(expectedResult, actualResult)
