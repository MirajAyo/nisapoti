from django.urls import path, include
from..views import views_auth, views_profile, views_post, views_chat
# from ..import views_auth
from django.urls import path

urlpatterns = [

# post
    path('upload', views_post.upload, name='upload'),
    # path('like-post', views.like_post, name='like-post'),
    path('like_post/', views_post.like_post, name='like_post'),
    
    path('post/<uuid:post_id>/', views_post.post_detail, name='post_detail'),
    path('post/<uuid:post_id>/comment/', views_post.comment_view, name='comment_view'),
    path('post/<uuid:post_id>/comment/<int:comment_id>/reply/', views_post.reply_comment_view, name='reply_comment_view'),
]
