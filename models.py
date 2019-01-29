from app import db, marsh

class board(): 
    # Check rows that are connected
    def checkRows(self,board, p1,p2): 
      numInEachRow = len(board[0])
      for i in range(0,len(board)): 
        x = sum(row.count(p1) for row in board[i])
        y = sum(row.count(p1) for row in board[i])
        if (x == numInEachRow): 
          return p1
        elif(y == numInEachRow): 
          return p2
      return False

    # Check col that are connected
    def checkCols(self,board,p1,p2): 
      numOfCol = len(board[0])
      for i in range(0,numOfCol): 
        #Iterate through each col 
        x = sum(board[j][i].count(p1) for j in range(len(board)))
        y = sum(board[j][i].count(p2) for j in range(len(board)))
        if (x == numOfCol): 
          return p1
        elif(y == numOfCol): 
          return p2
      return False

    # Check diagonals that are connected
    def checkDia(self,board,p1,p2): 
      numOfCol = len(board[0])
      numOfRow = len(board)

      # Check left diagonal 
      x = sum(board[i][i].count(p1) for i in range(numOfRow))
      y = sum(board[i][i].count(p2) for i in range(numOfRow))
      if (x == numOfCol): 
        return p1
      elif(y == numOfCol): 
        return p2    

      # Check right diagonal
      x = sum(board[i][numOfRow-i-1].count(p1) for i in range(numOfRow))
      y = sum(board[i][numOfRow-i-1].count(p2) for i in range(numOfRow))
      if (x == y == numOfCol): 
        return 'Draw'
      elif(x == numOfCol): 
        return p1
      elif(y == numOfCol): 
        return p2 
      return False

    def checkDraw(self,board):
      return sum(row.count('.') for row in board)


    def createBoard(self,row,col): 
      board = [['.']*col for i in range(row)]
      return board

    # Fill board with player_name  
    def fillBoard(self,board,allMoves): 
      for move in allMoves: 
        for row in range(4): 
          if move['move_type'] != 'QUIT':
            if board[row][move['input_column']-1] == '.': 
              board[row][move['input_column']-1] = move['player_name']
              break
      return board

# Define database models
class Game(db.Model):

    __tablename__ = 'game'

    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(50))
    winner  = db.Column(db.String(50))
    game_column = db.Column(db.Integer)
    game_row = db.Column(db.Integer)

    game_session = db.relationship('GameSession', backref='game', lazy='select', uselist=False)

    def __init__(self,state,winner, col, row): 
       self.state = state
       self.winner = winner
       self.game_column = col 
       self.game_row = row

    def __repr__(self): 
        return '<id {}>'.format(self.id)

class GameSession(db.Model): 

    __tablename__ = 'gamesession'

    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer)
    player2_id= db.Column(db.Integer)
    game_id= db.Column(db.Integer, db.ForeignKey('game.id'))

    moves = db.relationship('Moves', backref='gamemoves', lazy='select')

    def __init__(self,player1Id,player2Id,gameId): 
        self.player1_id = player1Id
        self.player2_id = player2Id
        self.game_id = gameId
    def __repr__(self): 
        return '<id {}>'.format(self.id)

class Moves(db.Model):

    __tablename__ = 'moves'

    id = db.Column(db.Integer, primary_key=True)
    move_number = db.Column(db.Integer)
    move_type = db.Column(db.String(50))
    input_column = db.Column(db.Integer)
    player_id = db.Column(db.Integer) 
    player_name = db.Column(db.String) 
    gamesession_id = db.Column(db.Integer, db.ForeignKey('gamesession.id'))

    
    def __init__(self,moveNum,moveType,inputCol,playerId,playerName,gameId):
        self.move_number = moveNum
        self.move_type = moveType
        self.input_column = inputCol
        self.player_id = playerId
        self.player_name = playerName
        self.gamesession_id = gameId
    def __repr__(self): 
        return '<id {}>'.format(self.id)
  
class Players(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), unique=True)

    def __init__(self,playerName): 
        self.player_name = playerName
    def __repr__(self): 
        return '<id {}>'.format(self.id)


# Schemas for database models
class MoveSchema(marsh.ModelSchema): 
    class Meta:
        fields = ('move_type', 'player_name', 'input_column')
        include_fk = True
        
class GameSessionSchema(marsh.ModelSchema): 
    class Meta:
        model = GameSession
        include_fk = True 
    moves = marsh.Nested(MoveSchema,many=True)

class GameSchema(marsh.ModelSchema): 
    class Meta:
        model = Game
    game_session = marsh.Nested(GameSessionSchema)

class PlayerSchema(marsh.ModelSchema): 
    class Meta:
        model = Players