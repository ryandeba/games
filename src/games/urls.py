from django.conf.urls import patterns, include, url

from django.contrib import admin

import chess, cardsAgainstHumanity, games

urlpatterns = patterns('',
	url(r'^chess/lobby/$', 'chess.views.lobby'),
	url(r'^chess/newGame/$', 'chess.views.newGame_view'),
	url(r'^chess/game/(?P<game_id>\d+)/piece/(?P<piece_id>\d+)/move/(?P<position>.+)', 'chess.views.movePiece'),
	url(r'^chess/game/(?P<game_id>\d+)', 'chess.views.game'),
	url(r'^chess$', 'chess.views.index'),

	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/submitAnswer/(?P<card_id>\d+)', 'cardsAgainstHumanity.views.submitAnswer'),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/chooseWinner/(?P<card_id>\d+)', 'cardsAgainstHumanity.views.chooseWinner'),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/submitMessage', 'cardsAgainstHumanity.views.submitMessage'),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/addBot', 'cardsAgainstHumanity.views.addBot'),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/start', 'cardsAgainstHumanity.views.startGame'),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)', 'cardsAgainstHumanity.views.game'),
	url(r'^cardsAgainstHumanity/newGame', 'cardsAgainstHumanity.views.newGame'),
	url(r'^cardsAgainstHumanity/lobby', 'cardsAgainstHumanity.views.lobby'),
	url(r'^cardsAgainstHumanity$', 'cardsAgainstHumanity.views.index'),

	url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'chess/login.html'}),
	url(r'^register/$', 'chess.views.register'),
	url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
	url(r'^$', 'games.views.index'),
)
