import random

class PuzzleGenerator:

   def new_puzzle(self):
    puzzleSolver = PuzzleSolver()
    puzzleSolver.solve_board(board = Board(), numberOfSolutionsToFind = 1, solveInRandomOrder = True)
    return puzzleSolver.solutions[0]

class PuzzleSolver:

  def __init__(self, board = None):
    self.solutions = []
    self.board = Board(board)

  def solve_board(self, board, numberOfSolutionsToFind, solveInRandomOrder = False):
    thisBoard = Board(board.getBoard())
    if thisBoard.isSolveable() == False:
      return
    nextUnsolvedIndexAndPossibleSolutions = thisBoard.getNextUnsolvedIndexAndPossibleValues()
    if (nextUnsolvedIndexAndPossibleSolutions['index']) >= 0:
      unsolvedIndex = nextUnsolvedIndexAndPossibleSolutions['index']
      possibleValues = nextUnsolvedIndexAndPossibleSolutions['possibleValues']
      if solveInRandomOrder:
        random.shuffle(possibleValues)
      for i in possibleValues:
        thisBoard.setIndexToValue(unsolvedIndex, str(i))
        self.solve_board(thisBoard, numberOfSolutionsToFind, solveInRandomOrder)
        if len(self.solutions) >= numberOfSolutionsToFind:
          return
    if thisBoard.isSolved():
      self.solutions.append(Board(thisBoard.getBoard()))
    return

  def findUpToNSolutions(self, n):
    self.solve_board(self.board, n)

  def getFirstSolution(self):
    self.findUpToNSolutions(1)
    if len(self.solutions) > 0:
      return self.solutions[0]
    return ''

class Board:

  VALID_VALUES = list('123456789')
  ROWS = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8],
    [9, 10, 11, 12, 13, 14, 15, 16, 17],
    [18, 19, 20, 21, 22, 23, 24, 25, 26],
    [27, 28, 29, 30, 31, 32, 33, 34, 35],
    [36, 37, 38, 39, 40, 41, 42, 43, 44],
    [45, 46, 47, 48, 49, 50, 51, 52, 53],
    [54, 55, 56, 57, 58, 59, 60, 61, 62],
    [63, 64, 65, 66, 67, 68, 69, 70, 71],
    [72, 73, 74, 75, 76, 77, 78, 79, 80]
  ]
  COLUMNS = [
    [0, 9, 18, 27, 36, 45, 54, 63, 72],
    [1, 10, 19, 28, 37, 46, 55, 64, 73],
    [2, 11, 20, 29, 38, 47, 56, 65, 74],
    [3, 12, 21, 30, 39, 48, 57, 66, 75],
    [4, 13, 22, 31, 40, 49, 58, 67, 76],
    [5, 14, 23, 32, 41, 50, 59, 68, 77],
    [6, 15, 24, 33, 42, 51, 60, 69, 78],
    [7, 16, 25, 34, 43, 52, 61, 70, 79],
    [8, 17, 26, 35, 44, 53, 62, 71, 80]
  ]
  SQUARES = [
    [0, 1, 2, 9, 10, 11, 18, 19, 20],
    [3, 4, 5, 12, 13, 14, 21, 22, 23],
    [6, 7, 8, 15, 16, 17, 24, 25, 26],
    [27, 28, 29, 36, 37, 38, 45, 46, 47],
    [30, 31, 32, 39, 40, 41, 48, 49, 50],
    [33, 34, 35, 42, 43, 44, 51, 52, 53],
    [54, 55, 56, 63, 64, 65, 72, 73, 74],
    [57, 58, 59, 66, 67, 68, 75, 76, 77],
    [60, 61, 62, 69, 70, 71, 78, 79, 80]
  ]

  def __init__(self, board = None):
    self.loadBoard(board)

  def __str__(self):
    result = ''
    for i in range(81):
      result += self.getValueAtIndex(i)
    return result

  def prettyPrint(self):
    result = ''
    for i in range(81):
      result += self.getValueAtIndex(i) + ' '
      if (i + 1) % 9 == 0:
        result += '\n'
      elif (i + 1) % 3 == 0:
        result += '| '
      if i == 26 or i == 53:
        result += '- - - | - - - | - - -\n'
    return result

  def getBoard(self):
    return self.cells

  def clearBoard(self):
     self.cells = ['0'] * 81

  def loadBoard(self, board = None):
    self.clearBoard()
    for i in range(len(board or '')):
      self.setIndexToValue(i, board[i])

  def setIndexToValue(self, boardIndex, value):
    if boardIndex >= 0 and boardIndex <= 80:
      self.cells[boardIndex] = self.convertToValidValue(value)

  def getValueAtIndex(self, boardIndex):
    return self.cells[boardIndex]

  def getUnsolvedIndexes(self):
    return filter(lambda index: self.getValueAtIndex(index) not in self.VALID_VALUES, range(81))

  def convertToValidValue(self, value):
    return str(value) if str(value) in self.VALID_VALUES else '0'

  def isSolved(self):
    return self.areRowsSolved() and self.areColumnsSolved() and self.areSquaresSolved()

  def isSolveable(self):
    #TODO: also make sure that all unsolved indexes have at least 1 possible value
    return self.areRowsValid() and self.areColumnsValid() and self.areSquaresValid()

  def getNextUnsolvedIndexAndPossibleValues(self):
    unsolvedIndexesAndSolutions = []

    unsolvedIndexes = self.getUnsolvedIndexes()
    for index in unsolvedIndexes:
      possibleValuesForThisIndex = self.getPossibleValuesForIndex(index)
      if len(possibleValuesForThisIndex) == 0:
        return {'index': -1, 'possibleValues' : possibleValuesForThisIndex}
      if len(possibleValuesForThisIndex) == 1:
        return {'index': index, 'possibleValues' : possibleValuesForThisIndex}
      unsolvedIndexesAndSolutions.append({'index': index, 'possibleValues': possibleValuesForThisIndex})
    return sorted(unsolvedIndexesAndSolutions, key = lambda k: len(k['possibleValues']))[0] if len(unsolvedIndexesAndSolutions) > 0 else {'index': -1}

  def getPossibleValuesForIndex(self, index):
    possibleValues = self.VALID_VALUES[:]

    row = int(index / 9)
    for i in range(9):
      thisValue = self.getValueAtIndex((row * 9) + i)
      if thisValue in possibleValues:
        possibleValues.pop(possibleValues.index(thisValue))

    col = index % 9
    for i in range(9):
      thisValue = self.getValueAtIndex(col)
      col += 9
      if thisValue in possibleValues:
        possibleValues.pop(possibleValues.index(thisValue))

    for i in range(len(self.SQUARES)):
      if index in self.SQUARES[i]:
        square = i
        break
    for i in self.SQUARES[square]:
      thisValue = self.getValueAtIndex(i)
      if thisValue in possibleValues:
        possibleValues.pop(possibleValues.index(thisValue))
    
    return possibleValues

  def areRowsValid(self):
    for row in self.ROWS:
      if self.areIndexesValid(row) == False:
        return False
    return True

  def areColumnsValid(self):
    for column in self.COLUMNS:
      if self.areIndexesValid(column) == False:
        return False
    return True

  def areSquaresValid(self):
    for square in self.SQUARES:
      if self.areIndexesValid(square) == False:
        return False
    return True

  def areIndexesValid(self, indexes):
    values = []
    for index in indexes:
      if self.getValueAtIndex(index) != '0':
        values.append(self.getValueAtIndex(index))
    if len(values) != len(set(values)):
      return False
    return True

  def areRowsSolved(self):
    for rowIndexes in self.ROWS:
      if self.areIndexesSolved(rowIndexes) == False:
        return False
    return True

  def areColumnsSolved(self):
    for columnIndexes in self.COLUMNS:
      if self.areIndexesSolved(columnIndexes) == False:
        return False
    return True 
  def areSquaresSolved(self):
    for squareIndexes in self.SQUARES:
      if self.areIndexesSolved(squareIndexes) == False:
        return False
    return True

  def areIndexesSolved(self, indexes):
    values = []
    for index in indexes:
      if self.getValueAtIndex(index) == '0':
        return False
      else:
        values.append(self.getValueAtIndex(index))
    if len(values) != len(set(values)):
      return False
    return True
