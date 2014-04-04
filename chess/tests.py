from django.test import TestCase

from chess.models import *

def setupGame():
	game = new_game()
	user1 = new_user(username = "1")
	user2 = new_user(username = "2")
	gameUser1 = game.addUser(user1)
	gameUser2 = game.addUser(user2)
	game.startGame()
	return (game, user1, user2, gameUser1, gameUser2)

class UtilityTests(TestCase):

	def test_new_game(self):
		game = new_game()
		self.assertEqual(game, Game.objects.get(id = game.id))

	def test_load_game_by_id(self):
		game = new_game()
		loadedGame = load_game_by_id(game.id)
		self.assertEqual(game, loadedGame)

	def test_loadPiecesByGame(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		self.assertEqual(32, len(load_pieces_by_game(game)))

	def test_convert_position_to_coordinates(self):
		self.assertEqual((1, 1), convert_position_to_coordinates("A1"))
		self.assertEqual((2, 2), convert_position_to_coordinates("B2"))
		self.assertEqual((3, 3), convert_position_to_coordinates("C3"))

	def test_convert_coordinates_to_position(self):
		self.assertEqual("A1", convert_coordinates_to_position((1, 1)))
		self.assertEqual("B2", convert_coordinates_to_position((2, 2)))
		self.assertEqual("C3", convert_coordinates_to_position((3, 3)))

	def test_get_position_by_offset(self):
		self.assertEqual("A1", get_position_by_offset("A1", 0, 0))
		self.assertEqual("B2", get_position_by_offset("A1", 1, 1))
		self.assertEqual("A1", get_position_by_offset("B2", -1, -1))
		self.assertEqual("", get_position_by_offset("A1", -1, -1))
		self.assertEqual("", get_position_by_offset("H8", 1, 1))

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

		self.assertEqual(False, gameUser1.is_black())
		self.assertEqual(None, gameUserNone)
		self.assertEqual(True, gameUser2.is_black())
		self.assertEqual(None, gameUser3)

	def test_startGame(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		self.assertEqual(True, game.is_active())

	def test_startGame_statusIsNotChangedIfStatusIsNotPending(self):
		game = new_game()
		game.status = GAMESTATUS["FINISHED"]
		user1 = User.objects.create(username = "1")
		user2 = User.objects.create(username = "2")

		game.addUser(user1)
		game.addUser(user2)

		game.startGame()

		self.assertEqual(False, game.is_active())

	def test_startGame_statusIsNotChangedIfThereAreNotTwoPlayers(self):
		game = new_game()
		game.startGame()
		self.assertEqual(False, game.is_active())

	def test_getGameUserCurrentTurn_returnsWhiteUserIfThereIsNoHistory(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		self.assertEqual(True, game.getGameUserCurrentTurn().is_white())

	def test_getGameUserCurrentTurn_returnsBlackIfWhiteMovedLast(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		game.get_piece_at_position("A2").moveToPosition("A3")

		self.assertEqual(True, game.getGameUserCurrentTurn().is_black())

	def test_getAvailableMoves(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		expectedResult = []
		actualResult = game.getAvailableMoves()

		self.maxDiff = None
		#self.assertEqual([], actualResult)
		self.assertTrue({'piece': game.get_piece_at_position('A2'), 'positions': ['A3', 'A4']} in actualResult)
		self.assertTrue({'piece': game.get_piece_at_position('B1'), 'positions': ['C3', 'A3']} in actualResult)

	def test_castling(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		game.get_piece_at_position("F1").position = ""
		game.get_piece_at_position("G1").position = ""
		game.get_piece_at_position("D1").position = ""
		game.get_piece_at_position("C1").position = ""
		game.get_piece_at_position("B1").position = ""

		game.get_piece_at_position("F8").position = ""
		game.get_piece_at_position("G8").position = ""
		game.get_piece_at_position("D8").position = ""
		game.get_piece_at_position("C8").position = ""
		game.get_piece_at_position("B8").position = ""

		king = game.get_piece_at_position("E1")
		self.assertEqual(["F1", "D1", "G1", "C1"], game.getAvailableMovesForPiece(king))

		king = game.get_piece_at_position("E8")
		self.assertEqual(["F8", "D8", "G8", "C8"], game.getAvailableMovesForPiece(king))

	def test_move_piece_to_position(self):
		game, user1, user2, gameUser1, gameUser2 = setupGame()

		game.move_piece_to_position(game.get_piece_at_position("E2").id, "E3")
		game.move_piece_to_position(game.get_piece_at_position("A7").id, "A6")
		game.move_piece_to_position(game.get_piece_at_position("D1").id, "F3")
		game.move_piece_to_position(game.get_piece_at_position("A6").id, "A5")
		game.move_piece_to_position(game.get_piece_at_position("F1").id, "C4")
		game.move_piece_to_position(game.get_piece_at_position("A5").id, "A4")
		game.move_piece_to_position(game.get_piece_at_position("F3").id, "F7")

		self.assertTrue(game.gameuser_is_in_check(gameUser2))

		#TODO: why does this need to get reloaded?
		gameUser2 = GameUser.objects.get(id = gameUser2.id)
		self.assertEqual(True, gameUser2.has_been_in_check())
