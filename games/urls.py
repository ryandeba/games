from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import chess

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'games.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

   #url(r'^admin/', include(admin.site.urls)),
	 url(r'^$', 'chess.views.index')
)
