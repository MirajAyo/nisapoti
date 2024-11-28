from django.urls import path, include
from..views import views_auth, views_profile, views_post, views_chat
# from ..import views_auth
from django.urls import path

urlpatterns = [

     # follow
    path('follow', views_profile.follow, name='follow'),

    path('search', views_profile.search, name='search'),
    path('settings', views_profile.settings, name='settings'),
    path('<str:pk>/', views_profile.profile, name='profile'),

    
]
