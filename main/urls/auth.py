from django.urls import path, include
from..views import views_auth, views_profile, views_post, views_chat
# from ..import views_auth
from django.urls import path



urlpatterns=[
    # path('', views_auth.index, name='index'),
     path('', views_auth.index, name='index'), 
    
   path('signin/', views_auth.signin, name='signin'), # Your custom login view
    path('signup/', views_auth.signup, name='signup'),
    path('logout/', views_auth.logout_view, name='logout'),
   
    
    
    
]





