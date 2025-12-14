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
                              UserNotesView, UserNotesHistoryView, UserNotesReportView)
from wxcloudrun.views.finance import (DashboardView, TransactionView, PlanningView, AssetView, 
                                      FixedItemView, FutureItemView, LoanView, ProfileView, AssetCorrectionView)
from django.conf.urls import url

urlpatterns = (
    # 计数器接口
    url(r'^^api/count(/)?$', counter),
    url(r'^^api/dinners/(?P<openId>\w+)(/)?$', DinnerView.as_view()),
    url(r'^^api/friend/dinners/(?P<openId>\w+)(/)?$', FriendDinnerView.as_view()),
    url(r'^^api/friends/(?P<openId>[\w\-]+)(/)?$', FriendView.as_view()),
    url(r'^^api/login(/)?$', LoginView.as_view()),
    url(r'^^api/users(/)?$', UserView.as_view()),
    url(r'^^api/dinnersLikes(/)?$', DinnerLikeView.as_view()),
    url(r'^^api/usernotes/(?P<openId>[\w-]+)(/)?$', UserNotesView.as_view()),
    url(r'^^api/usernoteshistory/(?P<openId>[\w-]+)(/)?$', UserNotesHistoryView.as_view()),
    url(r'^^api/usernotesreport/(?P<openId>[\w-]+)(/)?$', UserNotesReportView.as_view()),
    url(r'^^api/dashboard/summary/(?P<openId>\w+)(/)?$', DashboardView.as_view()),
    url(r'^^api/transactions/(?P<openId>\w+)(/)?$', TransactionView.as_view()),
    url(r'^^api/transactions/(?P<openId>\w+)/(?P<pk>\d+)(/)?$', TransactionView.as_view()),
    url(r'^^api/planning/summary/(?P<openId>\w+)(/)?$', PlanningView.as_view()),
    url(r'^^api/assets/(?P<openId>\w+)(/)?$', AssetView.as_view()),
    url(r'^^api/assets/(?P<openId>\w+)/(?P<pk>\d+)(/)?$', AssetView.as_view()),
    url(r'^^api/fixed-items/(?P<openId>\w+)(/)?$', FixedItemView.as_view()),
    url(r'^^api/fixed-items/(?P<openId>\w+)/(?P<pk>\d+)(/)?$', FixedItemView.as_view()),
    url(r'^^api/future-items/(?P<openId>\w+)(/)?$', FutureItemView.as_view()),
    url(r'^^api/future-items/(?P<openId>\w+)/(?P<pk>\d+)(/)?$', FutureItemView.as_view()),
    url(r'^^api/loans/(?P<openId>\w+)(/)?$', LoanView.as_view()),
    url(r'^^api/loans/(?P<openId>\w+)/(?P<pk>\d+)(/)?$', LoanView.as_view()),
    url(r'^^api/profile/(?P<openId>\w+)(/)?$', ProfileView.as_view()),
    url(r'^^api/assets/correction/(?P<openId>\w+)(/)?$', AssetCorrectionView.as_view()),
)
