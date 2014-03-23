from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import chess

urlpatterns = patterns('',
	 url(r'^$', 'chess.views.index'),
)
