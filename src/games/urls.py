from django.conf.urls import patterns, include, url

from django.contrib import admin

from games.apps.chess import views as chess_views
from games.apps.cardsAgainstHumanity import views as cah_views
from games.apps.common import views as common_views

urlpatterns = patterns('',
	url(r'^chess/lobby/$', chess_views.lobby),
	url(r'^chess/newGame/$', chess_views.newGame_view),
	url(r'^chess/game/(?P<game_id>\d+)/piece/(?P<piece_id>\d+)/move/(?P<position>.+)', chess_views.movePiece),
	url(r'^chess/game/(?P<game_id>\d+)', chess_views.game),
	url(r'^chess$', chess_views.index),

	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/submitAnswer/(?P<card_id>\d+)', cah_views.submitAnswer),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/chooseWinner/(?P<card_id>\d+)', cah_views.chooseWinner),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/submitMessage', cah_views.submitMessage),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/addBot', cah_views.addBot),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)/start', cah_views.startGame),
	url(r'^cardsAgainstHumanity/game/(?P<game_id>\d+)', cah_views.game),
	url(r'^cardsAgainstHumanity/newGame', cah_views.newGame),
	url(r'^cardsAgainstHumanity/lobby', cah_views.lobby),
	url(r'^cardsAgainstHumanity$', cah_views.index),

	url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'chess/login.html'}),
	url(r'^register/$', chess_views.register),
	url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
	url(r'^$', common_views.index),
)
