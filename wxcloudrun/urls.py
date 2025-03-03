"""wxcloudrun URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from wxcloudrun.views import (counter, UserView, DinnerView, LoginView, FriendDinnerView, DinnerLikeView, FriendView,
                              UserNotesView, UserNotesHistoryView)
from django.conf.urls import url

urlpatterns = (
    # 计数器接口
    url(r'^^api/count(/)?$', counter),
    url(r'^^api/dinners/(?P<openId>\w+)(/)?$', DinnerView.as_view()),
    url(r'^^api/friend/dinners/(?P<openId>\w+)(/)?$', FriendDinnerView.as_view()),
    url(r'^^api/friends/(?P<openId>\w+)(/)?$', FriendView.as_view()),
    url(r'^^api/login(/)?$', LoginView.as_view()),
    url(r'^^api/users(/)?$', UserView.as_view()),
    url(r'^^api/dinnersLikes(/)?$', DinnerLikeView.as_view()),
    url(r'^^api/usernotes/(?P<openId>\w+)(/)?$', UserNotesView.as_view()),
    url(r'^^api/usernoteshistory/(?P<openId>\w+)(/)?$', UserNotesHistoryView.as_view()),
)
