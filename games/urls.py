from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import chess

urlpatterns = patterns('',
	url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'chess/login.html'}),
	url(r'^register/$', 'chess.views.register'),
	url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

	url(r'^lobby/$', 'chess.views.lobby'),
	url(r'^newGame/$', 'chess.views.newGame_view'),
	url(r'^game/(?P<game_id>\d+)/piece/(?P<piece_id>\d+)/move/(?P<position>.+)', 'chess.views.movePiece'),
	url(r'^game/(?P<game_id>\d+)', 'chess.views.game'),
	url(r'^$', 'chess.views.index'),
)
