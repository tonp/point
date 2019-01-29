from flask import Flask, jsonify, request, json
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
CORS(app)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)
marsh = Marshmallow(app)

from models import board,Game,GameSession,Moves,Players,GameSchema,GameSessionSchema,MoveSchema,PlayerSchema

# Starting root
@app.route('/')
def index():
    return jsonify({'data': '98Point6 Drop-Token'})

# ROUTE : POST game
@app.route('/drop_token', methods=['POST'])
def postGame():
    try:
      # Add players
      addPlayer1 = Players(request.json['players'][0])
      addPlayer2 = Players(request.json['players'][1])
      db.session.add(addPlayer1)
      db.session.add(addPlayer2)

      # Add new Game
      newGame = Game('IN PROGRESS', '', request.json['columns'], request.json['rows'])
      db.session.add(newGame)
      db.session.commit()

      # Star new game session 
      session = GameSession(addPlayer1.id,addPlayer2.id,newGame.id)
      db.session.add(session)
      db.session.commit()

      return jsonify({'gameId': str(newGame.id)})
    except:
      return jsonify({"Error":"400"}),400


# POST /drop_token/{gameId}/{playerId} - Post a move 
@app.route('/drop_token/<int:game_id>/<int:player_id>', methods=['POST'])
def postMove(game_id,player_id): 
      
      # Get game session id
      query = GameSession.query.filter_by(game_id=game_id)
      gameses = GameSessionSchema(many=True)
      res = gameses.dump(query).data
      
      if not res:
        return jsonify({"Error":"404 - Game not found"}),404

      try:
        # Get moves number
        num = [row for row in res[0]['moves']]
        
        # Check if session is missing a player 
        inPlayers = False 
        if res[0]['player1_id'] == None or res[0]['player2_id'] == None: 
           inPlayers = checkPlayer(player_id)

        # Update session if new player
        if inPlayers: 
          query = GameSession.query.filter_by(game_id=game_id).first()
          player = Players.query.filter_by(id=player_id).first()
          p = PlayerSchema()
          s = p.dump(player).data
          if res[0]['player1_id'] == None: 
            query.player1_id = player_id
          else: 
            query.player2_id = player_id
          db.session.commit()
          # Update Moves
          query = Moves.query.filter_by(player_id=-1).all()
          for x in range(len(query)): 
            query[x].player_name = s['player_name']
            query[x].player_id = s['id']
            db.session.commit()
          m = MoveSchema()

        # Get player name 
        query = Players.query.filter_by(id=player_id)
        p = PlayerSchema(many=True)
        player = p.dump(query).data

        
        #Input moves
        col = request.json['column']
        newMove = Moves(len(num)+1, 'MOVE',col,player_id, str(player[0]['player_name']), res[0]['id'])
        db.session.add(newMove)
        db.session.commit()

        link = str(game_id)+'/moves/'+ str(len(num)+1)

        checkGame(res[0]['id'])

        return jsonify({'move':link})
      except: 
        return jsonify({"Error":"400"}),400

# Check if player exists in players table
def checkPlayer(player_id): 

      # Wuery session
      query = Players.query.filter_by(id=player_id)
      pl = PlayerSchema(many=True)
      res = pl.dump(query).data

      if res[0]['id'] == player_id: 
        return True
      else: 
        return False

# Check game logic
def checkGame(gamesession_id): 

      # Get Moves 
      query = Moves.query.filter_by(gamesession_id=gamesession_id)
      n = MoveSchema(many=True)
      m = n.dump(query).data
      allMoves = [dict(item) for item in m]

      # Get player 1, player 2
      t = GameSession.query.filter_by(game_id=gamesession_id)
      s = GameSessionSchema(many=True)
      gameSess = s.dump(t).data
      p1id = gameSess[0]['player1_id']
      p2id = gameSess[0]['player2_id']

      t = Players.query.filter_by(id=p1id)
      s = PlayerSchema(many=True)
      b = s.dump(t).data
      player1name = b[0]['player_name']

      a = Players.query.filter_by(id=p2id)
      e = PlayerSchema(many=True)
      r = e.dump(a).data
      player2name = r[0]['player_name']

      # Check board for winners 
      newBoard = board()
      grid = newBoard.createBoard(4,4)
      grid = newBoard.fillBoard(grid, allMoves)
      winner = ''
      col = newBoard.checkCols(grid,player1name, player2name)
      row= newBoard.checkRows(grid,player1name, player2name)
      dia= newBoard.checkDia(grid,player1name, player2name)
      draw = newBoard.checkDraw(grid)

      if col: 
        winner = col
      elif row: 
        winner = row
      elif dia:
        winner = dia
      
      if (draw == 0):
        query = Game.query.filter_by(id=gameSess[0]['game_id']).first()
        query.state = 'DRAW'
        query.winner = ''
        db.session.commit()
      if (winner == player2name or winner == player1name):
        query = Game.query.filter_by(id=gameSess[0]['game_id']).first()
        query.state = 'DONE'
        query.winner = winner
        db.session.commit()


  

# GET /drop_token/{gameId}/moves/{move_number} - Return the move
@app.route('/drop_token/<int:game_id>/moves/<int:moveInt>')
def getMoveById(game_id,moveInt): 
      # Get session id
      sess = GameSession.query.filter_by(game_id=game_id)
      n = GameSessionSchema(many=True)
      res = n.dump(sess).data  

      if not res:
        return jsonify({"Error":"404 - Game not found"}),404
      
      try: 
        # Get move
        m = Moves.query.filter_by(gamesession_id=res[0]['id'], move_number=moveInt)
        move_sch = MoveSchema(many=True)
        res = move_sch.dump(m).data
        return jsonify(res[0])
      except: 
        return jsonify({"Error":"400"}),400

# GET /drop_token - Return all in-progress games
@app.route('/drop_token', methods=['GET'])
def getGame(): 
      query = Game.query.filter_by(state="IN PROGRESS").all()
      game_sch = GameSchema(many=True)
      res = [str(item['id']) for item in game_sch.dump(query).data]
      return jsonify({'games': res})

# GET /drop_token/{gameId} - Get the state of the game.
@app.route('/drop_token/<int:game_id>', methods=['GET'])
def getGameState(game_id): 

      # Get state
      query = Game.query.filter_by(id=game_id)
      game_sch = GameSchema(many=True)
      res = game_sch.dump(query).data

      if not res:
        return jsonify({"Error":"404 - Game not found"}),404

      try:
        # Get player 1, player 2
        t = GameSession.query.filter_by(game_id=game_id)
        s = GameSessionSchema(many=True)
        b = s.dump(t).data
        p1id = b[0]['player1_id']
        p2id = b[0]['player2_id']

        player1name = ''
        player2name = ''

        # Set name
        if p1id is not None: 
          
          t = Players.query.filter_by(id=p1id)
          s = PlayerSchema(many=True)
          b = s.dump(t).data
          player1name = b[0]['player_name']

        if p2id is not None:
          
          a = Players.query.filter_by(id=p2id)
          e = PlayerSchema(many=True)
          r = e.dump(a).data
          player2name = r[0]['player_name']


        if res[0]['state'] == 'IN PROGRESS': 
          return jsonify({'players':[player1name, player2name], 
            'state':res[0]['state']})
        elif res[0]['state'] == 'DONE' or res[0]['state'] == 'DRAW': 
          return jsonify({'players':[player1name, player2name], 
            'state':res[0]['state'], 'winner': res[0]['winner']})
        else: 
          return jsonify('')
      except: 
          return jsonify({"Error":"400"}),400

# GET list of the moves play by game_id
@app.route('/drop_token/<int:game_id>/moves', methods=['GET'])
def getMoves(game_id): 

      # Get session id
      sess = GameSession.query.filter_by(game_id=game_id)
      n = GameSessionSchema(many=True)
      res = n.dump(sess).data
      if not res:
        return jsonify({"Error":"404 - Game not found"}),404

      try:
        # Get moves by sessId
        m = Moves.query.filter_by(gamesession_id=res[0]['id'])
        move_sch = MoveSchema(many=True)
        res = move_sch.dump(m).data
        return jsonify({'moves': res})
      except: 
        return jsonify({"Error":"400"}),400


#DELETE /drop_token/{gameId}/{playerId} - Player quits from game
@app.route('/drop_token/<int:game_id>/<int:player_id>', methods=['DELETE'])
def quitGame(game_id,player_id): 

      # Get game session id
      query = GameSession.query.filter_by(game_id=game_id)
      gameses = GameSessionSchema(many=True)
      res = gameses.dump(query).data

      if not res:
        return jsonify({"Error":"404 - Game not found"}),404

      try:
        # Get moves number
        num = [row for row in res[0]['moves']]

        # Get the player
        playerquery = Players.query.filter_by(id=player_id).first()
        n = PlayerSchema()
        player = n.dump(playerquery).data
        db.session.commit()

        updateMoves = Moves.query.filter_by(player_id=player_id).all()
        for x in range(len(updateMoves)):
          updateMoves[x].player_id = -1
          db.session.commit()

        # Update the moves
        newMove = Moves(len(num)+1, 'QUIT',None,player_id, str(player['player_name']), res[0]['id'])
        db.session.add(newMove)
        db.session.commit()

        # Delete the player 
        db.session.delete(playerquery)
        db.session.commit()

        # Update the game sesson  
        if res[0]['player1_id'] == player_id: 
          query[0].player1_id = None
        else: 
          query[0].player2_id = None
        db.session.commit()

        return jsonify({'Player': 'Player is deleted'})
      except: 
        return jsonify({"Error":"400"}),400


if __name__ == '__main__':

  app.run(debug=True)