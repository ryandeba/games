$(function(){

	cardsAgainstHumanity.AnswerCard = Backbone.Model.extend({
		idAttribute: "card_id",

		defaults: {
			winner: false,
			faceUp: true,
			submittedBy: ""
		}
	});

	cardsAgainstHumanity.AnswerCards = Backbone.Collection.extend({
		model: cardsAgainstHumanity.AnswerCard
	});

	cardsAgainstHumanity.AnswerCardView = Backbone.Marionette.ItemView.extend({
		template: "#template-answercard",

		attributes: {
			'class': 'col-md-2 col-sm-3 col-xs-6'
		},

		initialize: function(){
			this.listenTo(this.model, "change", this.render);
		},

		events: {
			"click": "onClick"
		},

		onClick: function(){
			cardsAgainstHumanity.vent.trigger("game:submitAnswer", this.model);
		}
	});

	cardsAgainstHumanity.AnswerCardsView = Backbone.Marionette.CollectionView.extend({
		itemView: cardsAgainstHumanity.AnswerCardView
	});

});
