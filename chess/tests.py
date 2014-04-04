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

	def test_getGameUserCurrentTurn_returnsBlackIfWhiteMovedLast(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		game.getPieceAtPosition("A2").moveToPosition("A3")

		self.assertEqual(True, game.getGameUserCurrentTurn().isBlack())

	def test_getAvailableMoves(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		expectedResult = []
		actualResult = game.getAvailableMoves()

		self.maxDiff = None
		#self.assertEqual([], actualResult)
		self.assertTrue({'piece': game.getPieceAtPosition('A2'), 'positions': ['A3', 'A4']} in actualResult)
		self.assertTrue({'piece': game.getPieceAtPosition('B1'), 'positions': ['C3', 'A3']} in actualResult)

	def test_castling(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		game.getPieceAtPosition("F1").position = ""
		game.getPieceAtPosition("G1").position = ""
		game.getPieceAtPosition("D1").position = ""
		game.getPieceAtPosition("C1").position = ""
		game.getPieceAtPosition("B1").position = ""

		game.getPieceAtPosition("F8").position = ""
		game.getPieceAtPosition("G8").position = ""
		game.getPieceAtPosition("D8").position = ""
		game.getPieceAtPosition("C8").position = ""
		game.getPieceAtPosition("B8").position = ""

		king = game.getPieceAtPosition("E1")
		self.assertEqual(["F1", "D1", "G1", "C1"], game.getAvailableMovesForPiece(king))

		king = game.getPieceAtPosition("E8")
		self.assertEqual(["F8", "D8", "G8", "C8"], game.getAvailableMovesForPiece(king))
