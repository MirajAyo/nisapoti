from datetime import timedelta
from itertools import chain
import logging
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from ..models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


import random


from django.contrib.auth.models import User, auth
# from .forms import CartForm

#import winsound  # For Windows only, use appropriate library for your OS
from django.conf import settings
import os


# Create your views here.
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password ==password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                    messages.info(request, 'Username taken')
                    return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # log user and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                
                # create a profile objects for new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password not matching')
            return redirect('signup')
    else:
        return render(request, 'sign-up.html')
    
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Both fields are required.")
            return redirect('signin')

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('signin')
    return render(request, 'sign-in.html')

def logout_view(request):
    logout(request)  # Log out the user
    # Redirect to 'signin' URL by its name
    return redirect(reverse('signin'))


@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    # Fetch posts from users the current user is following
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    user_following_list = [user.user for user in user_following]
    following_posts = Post.objects.filter(user__in=user_following_list).annotate(comment_count=Count('comments')).order_by('-created_at')

    # Fetch posts from the current user
    user_posts = Post.objects.filter(user=request.user).annotate(comment_count=Count('comments')).order_by('-created_at')

    # Combine both querysets
    feed_list = following_posts | user_posts

    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    # Add logging to inspect the notifications queryset
    logger = logging.getLogger(__name__)
    logger.info(f"Notifications: {notifications}")

    # Suggestions
    all_users = User.objects.all()
    user_following_all = [User.objects.get(username=user.user) for user in user_following]
    new_suggestions_list = [x for x in all_users if (x not in user_following_all and x != request.user)]
    random.shuffle(new_suggestions_list)

    suggestions_username_profile_list = Profile.objects.filter(user__in=new_suggestions_list)[:4]

    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        comment_text = request.POST.get('comment_text')
        parent_id = request.POST.get('parent_id')
        
        post = Post.objects.get(id=post_id)
        if parent_id:
            parent_comment = Comment.objects.get(id=parent_id)
            Comment.objects.create(post=post, user=user_object, text=comment_text, parent=parent_comment)
        else:
            Comment.objects.create(post=post, user=user_object, text=comment_text)

        return redirect('index')
    # Retrieve the current user's notifications
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    context = {
        'notifications': notifications,
        'user_profile': user_profile, 
        'posts': feed_list, 
        'suggestions_username_profile_list': suggestions_username_profile_list,
        
        
    }

    return render(request, 'index.html',context)


def root(request):
    # This can either render a homepage or redirect to another page like login
    return redirect('auth:index')  # Or render('home.html')
