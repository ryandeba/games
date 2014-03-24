$(function(){
	Chess = new Backbone.Marionette.Application();
	var app = Chess;

	app.addInitializer(function(){
		new CellsView({collection: new Cells()}).render();
	});

	var syncPiecesToCells = function(pieces, cells){
		cells.each(function(cell){
			cell.set("piece", pieces.findWhere({position: cell.get("position")}));
		});
	};

	var Piece = Backbone.Model.extend({
		isBlack: function(){ return true; },
		isWhite: function(){ return true; },
		isPawn: function(){ return true; },
		isRook: function(){ return false; },
		isKnight: function(){ return false; },
		isBishop: function(){ return false; },
		isQueen: function(){ return false; },
		isKing: function(){ return false; }
	});

	var Pieces = Backbone.Collection.extend({
		model: Piece
	});

	var Cell = Backbone.Model.extend({
	});

	var Cells = Backbone.Collection.extend({
		model: Cell,
		initialize: function(){
			var columns = "ABCDEFGH".split("");
			for (var x = 0; x < 8; x++){
				for (var y = 8; y > 0; y--){
					var position = columns[x] + y;
					this.add({position: position});
				}
			}
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
			app.vent.trigger("cell:click", this.model);
		},
		onRender: function(){
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
		}
	});

	var CellsView = Backbone.Marionette.CollectionView.extend({
		el: ".chessboard",
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
});
