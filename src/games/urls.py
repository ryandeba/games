from django.conf.urls import patterns, include, url

from django.contrib import admin

from games.apps.chess import views as chess_views
from games.apps.cardsAgainstHumanity import views as cardsAgainstHumanity_views
import games

urlpatterns = patterns('',
	url(r'^chess/lobby/$', chess_views.lobby),
	url(r'^chess/newGame/$', chess_views.newGame_view),
	url(r'^chess/game/(?P<game_id>\d+)/piece/(?P<piece_id>\d+)/move/(?P<position>.+)', chess_views.movePiece),
	url(r'^chess/game/(?P<game_id>\d+)', chess_views.game),
	url(r'^chess$', chess_views.index),

	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/submitAnswer/(?P<card_id>\d+)', cardsAgainstHumanity_views.submitAnswer),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/chooseWinner/(?P<card_id>\d+)', cardsAgainstHumanity_views.chooseWinner),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/submitMessage', cardsAgainstHumanity_views.submitMessage),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/addBot', cardsAgainstHumanity_views.addBot),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/start', cardsAgainstHumanity_views.startGame),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)', cardsAgainstHumanity_views.game),
	url(r'^cardsAgainstHumanity/newGame', cardsAgainstHumanity_views.newGame),
	url(r'^cardsAgainstHumanity/lobby', cardsAgainstHumanity_views.lobby),
	url(r'^cardsAgainstHumanity$', cardsAgainstHumanity_views.index),

	url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'chess/login.html'}),
	url(r'^register/$', chess_views.register),
	url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
	url(r'^$', 'games.views.index'),
)
