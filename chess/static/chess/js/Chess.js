$(function(){
	Chess = new Backbone.Marionette.Application();
	var app = Chess;

	var Router = Backbone.Router.extend({
		routes: {
			"game/:id": "game",
			"": "lobby"
		},
		game: function(id){ app.vent.trigger("showGame", id); },
		lobby: function(){ app.vent.trigger("showLobby"); }
	});
	new Router();

	app.addRegions({
		"mainRegion": "#main"
	});

	app.addInitializer(function(){
		this.listenTo(this.vent, "newGame", newGame);
		this.listenTo(this.vent, "showGame", showGame);
		this.listenTo(this.vent, "showLobby", showLobby);

		Backbone.history.start();
	});

	var showLobby = function(){
		app.mainRegion.show(new LobbyView({collection: new LobbyGames()}));
	};

	var showGame = function(id){
		game = new Game({id: id});
		app.mainRegion.show(new GameLayout({model: game}));
	};

	var newGame = function(){
		$.ajax({
			url: "/newGame/",
			success: function(response){
				showGame(response.game_id);
			}
		});
	};

	var Game = Backbone.Model.extend({
		initialize: function(){
			var self = this;
			this.set("cells", new Cells());
			this.set("pieces", new Pieces());
			this.set("players", new Players());
			this.set("history", new HistoryCollection());

			this.set("pollTimeout", undefined);

			this.listenTo(this.get("pieces"), "piece:select", this.selectPiece);
			this.listenTo(this, "change:selectedPiece", this.showAvailableMoves);
			this.listenTo(this.get("cells"), "cell:moveHere", this.moveSelectedPieceToCell);
			this.listenTo(this, "destroy", this.clearPollTimeout);

			this.load();
		},
		defaults: {
			'status': 0,
			'lastUpdated': 0
		},
		clearPollTimeout: function(){
			window.clearTimeout(this.get("pollTimeout"));
		},
		load: function(){
			var self = this;
			self.clearPollTimeout();
			$.ajax({
				url: "/game/" + self.get("id") + '?lastUpdated=' + self.get("lastUpdated"),
				complete: function(){
					if (self.get("status") != 2){
						self.set("pollTimeout", setTimeout(function(){ self.load(); }, 2000));
					}
				},
				success: function(response){
					if (response.status == undefined) //TODO: implement a better way to check if there is no data
						return;

					self.set("status", response.status);
					self.set("lastUpdated", response.lastUpdated);
					self.set("selectedPiece", undefined);
					self.get("pieces").set(response.pieces, {remove: false});
					self.get("players").set(response.players, {remove: false});
					self.get("history").set(response.history, {remove: false});
					self.set("currentturn_player_id", response.currentturn_player_id);
					self.set("winner_player_id", response.winner_player_id);

					self.syncColorsToPieces();
					self.syncPiecesToCells();
					self.syncAvailableMovesToPieces(response.moves);
					self.syncDataToPlayers();
				}
			});
		},
		syncColorsToPieces: function(){
			var players = this.get("players");
			this.get("pieces").each(function(piece){
				var player = players.findWhere({id: piece.get("player_id")});
				if (player){
					piece.set("color", player.get("color"));
				}
			});
		},
		syncPiecesToCells: function(){
			var pieces = this.get("pieces");
			this.get("cells").each(function(cell){
				cell.set("piece", pieces.findWhere({position: cell.get("position")}));
			});
		},
		syncAvailableMovesToPieces: function(moves){
			this.get("pieces").each(function(piece){
				var movesForThisPiece = _.findWhere(moves, {id: piece.get("id")});
				if (movesForThisPiece){
					piece.set("moves", movesForThisPiece.positions);
				} else {
					piece.set("moves", []);
				}
			});
		},
		syncDataToPlayers: function(){
			var self = this;
			self.get("players").each(function(player){
				var isMyTurn = player.get("id") == self.get("currentturn_player_id");
				player.set("isMyTurn", isMyTurn);
			});
		},
		selectPiece: function(piece){
			this.set("selectedPiece", piece);
		},
		showAvailableMoves: function(){
			var self = this;
			self.get("cells").each(function(cell){
				cell.set("possibleMove", false);
			});

			var piece = self.get("selectedPiece");
			if (piece == undefined){
				return;
			}
			_.each(piece.get("moves"), function(position){
				var cell = self.get("cells").findWhere({position: position});
				if (cell){
					cell.set("possibleMove", true);
				}
			});
		},
		moveSelectedPieceToCell: function(cell){
			var self = this;
			var selectedPiece = self.get("selectedPiece");
			$.ajax({
				url: "/game/" + self.get("id") + "/piece/" + selectedPiece.get("id") + "/move/" + cell.get("position"),
				success: function(response){ self.load(); }
			});
		},
		getWinner: function(){
			var winnerID = this.get("winner_player_id")
			return this.get("players").findWhere({id: winnerID});
		}
	});

	var GameStatusView = Backbone.Marionette.ItemView.extend({
		template: "#statusTemplate",
		initialize: function(){
			this.listenTo(this.model, "change", this.render);
		},
		serializeData: function(){
			var data = this.model.toJSON();

			data.currentTurnName = "";
			var currentTurnPlayer = this.model.get("players").findWhere({isMyTurn: true});
			if (currentTurnPlayer){
				data.currentTurnName = currentTurnPlayer.get("username");
			}

			data.resolution = "stalemate";
			var winner = this.model.getWinner();
			if (winner){
				data.resolution = "checkmate - " + winner.get("username") + " wins!";
			}
			return data;
		}
	});

	var Player = Backbone.Model.extend({
		defaults: {
			isMyTurn: false
		}
	});

	var Players = Backbone.Collection.extend({
		model: Player
	});

	var PlayerView = Backbone.Marionette.ItemView.extend({
		initialize: function(){
			this.listenTo(this.model, "change", this.render);
		},
		template: "#playerTemplate",
		tagName: "li"
	});

	var PlayersView = Backbone.Marionette.CompositeView.extend({
		template: "#playersTemplate",
		itemView: PlayerView,
		itemViewContainer: "#players_list"
	});

	var Piece = Backbone.Model.extend({
		isBlack: function(){ return this.get("color") == "BLACK"; },
		isWhite: function(){ return this.get("color") == "WHITE"; },

		isPawn: function(){ return this.get("type") == "PAWN"; },
		isRook: function(){ return this.get("type") == "ROOK"; },
		isKnight: function(){ return this.get("type") == "KNIGHT"; },
		isBishop: function(){ return this.get("type") == "BISHOP"; },
		isQueen: function(){ return this.get("type") == "QUEEN"; },
		isKing: function(){ return this.get("type") == "KING"; }
	});

	var Pieces = Backbone.Collection.extend({
		model: Piece
	});

	var PieceView = Backbone.Marionette.ItemView.extend({
		initialize: function(){
			this.listenTo(this.model, "change", this.render);
		},
		tagName: "span",
		template: "#pieceTemplate",
		onRender: function(){
			this.$el.removeClass("white black pawn rook knight bishop queen king");

			if (this.model.isWhite()){
				this.$el.addClass("white");
			} else {
				this.$el.addClass("black");
			}

			if (this.model.isPawn()) this.$el.addClass("pawn");
			if (this.model.isRook()) this.$el.addClass("rook");
			if (this.model.isKnight()) this.$el.addClass("knight");
			if (this.model.isBishop()) this.$el.addClass("bishop");
			if (this.model.isQueen()) this.$el.addClass("queen");
			if (this.model.isKing()) this.$el.addClass("king");
			if (this.model.get("position") == "") this.$el.addClass("captured");
		}
	});

	var PiecesView = Backbone.Marionette.CompositeView.extend({
		template: "#piecesTemplate",
		itemView: PieceView,
		itemViewContainer: "#pieces_list"
	});

	var Cell = Backbone.Model.extend({
	});

	var Cells = Backbone.Collection.extend({
		model: Cell,
		initialize: function(){
			var columns = "ABCDEFGH".split("");
			for (var y = 8; y > 0; y--){
				for (var x = 0; x < 8; x++){
					var position = columns[x] + y;
					this.add({position: position});
				}
			}
		}
	});

	var History = Backbone.Model.extend({
	});

	var HistoryCollection = Backbone.Collection.extend({
		model: History,
		comparator: function(model){
			return parseInt(model.get("id"));
		}
	});

	var HistoryView = Backbone.Marionette.ItemView.extend({
		initialize: function(){
			this.listenTo(this.model, "change", this.render);
		},
		template: "#historyTemplate",
		tagName: "li"
	});

	var HistoryCollectionView = Backbone.Marionette.CompositeView.extend({
		template: "#historyListTemplate",
		itemView: HistoryView,
		itemViewContainer: "#history_list"
	});

	var GameLayout = Backbone.Marionette.Layout.extend({
		onRender: function(){
			this.chessboardRegion.show(new CellsView({collection: this.model.get("cells")}));
			this.statusRegion.show(new GameStatusView({model: this.model}));
			this.playersRegion.show(new PlayersView({collection: this.model.get("players")}));
			this.historyRegion.show(new HistoryCollectionView({collection: this.model.get("history")}));
			this.piecesRegion.show(new PiecesView({collection: this.model.get("pieces")}));
		},
		onBeforeClose: function(){
			this.model.trigger("destroy");
		},
		template: "#gameTemplate",
		regions: {
			"chessboardRegion": "#game_chessboard",
			"statusRegion": "#game_status",
			"playersRegion": "#game_players",
			"historyRegion": "#game_history",
			"piecesRegion": "#game_pieces"
		}
	});

	var CellView = Backbone.Marionette.ItemView.extend({
		initialize: function(){
			this.listenTo(this.model, "change", this.render);
		},
		tagName: "td",
		template: "#cellTemplate",
		events: {
			"click": "onClick"
		},
		onClick: function(){
			if (this.model.get("possibleMove")){
				this.model.trigger("cell:moveHere", this.model);
			}
			else if (this.model.get("piece")){
				this.model.get("piece").trigger("piece:select", this.model.get("piece"));
			}
		},
		onRender: function(){
			this.$el.removeClass("white black pawn rook knight bishop queen king");
			var piece = this.model.get("piece");
			if (piece != undefined){
				if (piece.isWhite()){
					this.$el.addClass("white");
				} else {
					this.$el.addClass("black");
				}

				if (piece.isPawn()) this.$el.addClass("pawn");
				if (piece.isRook()) this.$el.addClass("rook");
				if (piece.isKnight()) this.$el.addClass("knight");
				if (piece.isBishop()) this.$el.addClass("bishop");
				if (piece.isQueen()) this.$el.addClass("queen");
				if (piece.isKing()) this.$el.addClass("king");
			}

			if (this.model.get("possibleMove") == true){
				this.$el.addClass("highlight");
			} else {
				this.$el.removeClass("highlight");
			}
		}
	});

	var CellsView = Backbone.Marionette.CollectionView.extend({
		render: function(){
			var $el = $("<div></div>");
			for (var i = 0; i < 8; i++){
				var $tr = $("<tr><td>" + (8 - i) + "</td></tr>");
				for (var j = 0; j < 8; j++){
					$tr.append(new CellView({model: this.collection.at((i * 8) + j)}).render().$el);
				}
				$el.append($tr);
			}
			$el.append("<tr> <td></td> <td>A</td> <td>B</td> <td>C</td> <td>D</td> <td>E</td> <td>F</td> <td>G</td> <td>H</td> </tr>");
			this.$el.html($el.children());
		}
	});

	var LobbyGames = Backbone.Collection.extend({
		initialize: function(){
			this.refresh();
		},
		refresh: function(){
			var self = this;
			$.ajax({
				url: "/lobby/",
				success: function(response){
					self.reset(response);
				}
			});
		}
	});

	var LobbyGameView = Backbone.Marionette.ItemView.extend({
		initialize: function(){
			this.listenTo(this.model, "change", this.render);
			this.listenTo(this.model, "remove", this.remove);
		},
		template: "#lobbyGameTemplate"
	});

	var LobbyView = Backbone.Marionette.CompositeView.extend({
		initialize: function(){
			this.listenTo(this.collection, "reset", this.render);
		},
		events: {
			"click .js-btn-refresh": "refresh",
			"click .js-btn-newgame": "newGame"
		},
		template: "#lobbyTemplate",
		itemView: LobbyGameView,
		itemViewContainer: "#gamelist",
		refresh: function(){
			this.collection.refresh();
		},
		newGame: function(){
			app.vent.trigger("newGame");
		}
	});
});
