from datetime import timedelta
from itertools import chain
import logging
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

import winsound  # For Windows only, use appropriate library for your OS
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
    logout(request)
    # next_url = request.GET.get('next', 'signin')  # Default to 'signin' if not found
    return redirect(signin)

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


@login_required(login_url='signin')
def sugest(request):
    # Suggestions
    all_users = User.objects.all()
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    user_following_all = [User.objects.get(username=user.user) for user in user_following]
    new_suggestions_list = [x for x in all_users if (x not in user_following_all and x != request.user)]
    random.shuffle(new_suggestions_list)

    suggestions_username_profile_list = Profile.objects.filter(user__in=new_suggestions_list)[:4]
    return render(request, 'sugest.html', {'suggestions_username_profile_list': suggestions_username_profile_list},)



@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST.get('caption', '').strip()  # Default to empty string if not provided

        # Ensure at least one field is provided
        if not image and not caption:
            messages.error(request, "You must provide either an image or a caption.")
            return redirect('index')  # Redirect back to the feed or upload page

        # Create the post
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        messages.success(request, "Your post was uploaded successfully.")
        return redirect('index')
    else:
        return redirect('index')



@login_required(login_url='signin')
def recharge (request):
    return render (request, 'recharge.html')


@login_required(login_url='signin')
def search (request):
    user_object= User.objects.get(username=request.user.username)
    user_profile=Profile.objects.get(user=user_object)

    if request.method=='POST':
        username=request.POST['username']
        username_object=User.objects.filter(username__icontains=username)

        username_profile=[]
        username_profile_list=[]

        for users in username_object:
            username_profile.append(users.id)
        
        for ids in username_profile:
            profile_lists=Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

            username_profile_list=list(chain(*username_profile_list))
           
    return render(request, 'search.html', {'user_profile':user_profile,'username_profile_list':username_profile_list})

@login_required(login_url='signin')
def like_post(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        username = request.user.username
        post_id = request.POST.get('post_id')
        post = Post.objects.get(id=post_id)

        # Check if the user has already liked the post
        like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

        if like_filter is None:
            # User has not liked the post, so create a new like
            new_like = LikePost.objects.create(post_id=post_id, username=username)
            new_like.save()
            post.no_of_likes += 1
            post.save()
            liked = True
        else:
            # User has already liked the post, so remove the like
            like_filter.delete()
            post.no_of_likes -= 1
            post.save()
            liked = False

        return JsonResponse({'liked': liked, 'no_of_likes': post.no_of_likes})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)




@login_required(login_url='signin')
def videos (request):
    return render(request, 'videos.html')
@login_required(login_url='signin')
def favorites (request):
    return render (request, 'favorites.html')


@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)
    user_wallet = request.user.wallet

    # follow
    follower = request.user.username
    user = pk
    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    follower_objects = FollowersCount.objects.filter(user=user_object)
    following_objects = FollowersCount.objects.filter(follower=request.user)
    followers = [obj.follower for obj in follower_objects]
    following = [obj.user for obj in following_objects]

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,

        'followers': followers,
        'following': following,
        
        'balance': user_wallet.balance,
    }

    if request.user != user_object:
        context['recipient'] = user_object

    return render(request, 'profile.html', context)

def profile_view(request):
    # Redirect to the logged-in user's profile
    return redirect('profile', pk=request.user.username)


@login_required(login_url='signin')
def follow (request):
    if request.method=='POST':
        follower=request.POST['follower']
        user=request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower=FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower=FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
    else:
        return redirect('/')

@login_required(login_url='signin')
def shop (request):
    return render (request, 'shop.html')
@login_required(login_url='signin')
def shop_details(request):
    return render (request, 'shop_details.html')


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        if 'image' in request.FILES:
            user_profile.profileimg = request.FILES['image']
            user_profile.bio = request.POST.get('bio', '')
            user_profile.location = request.POST.get('location', '')
            user_profile.save()
            messages.success(request, 'Profile updated successfully.')
        elif 'old_password' in request.POST:
            password_change_form = PasswordChangeForm(request.user, request.POST)
            if password_change_form.is_valid():
                user = password_change_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been updated.')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            user_profile.bio = request.POST.get('bio', '')
            user_profile.location = request.POST.get('location', '')
            user_profile.save()
            messages.success(request, 'Profile updated successfully.')

        return redirect('settings')
    else:
        password_change_form = PasswordChangeForm(request.user)
        return render(request, 'settings.html', {
            'user_profile': user_profile,
            'password_change_form': password_change_form
        })
# @login_required
# def post_detail(request, post_id):
#     post = get_object_or_404(Post, id=post_id)
#     user_object = User.objects.get(username=request.user.username)
#     user_profile = Profile.objects.get(user=user_object)

#     comments = Comment.objects.filter(post=post, parent=None)
#     comment_count = comments.count()
#     return render(request, 'post_detail.html', {'post': post, 'comments': comments, 'user_profile': user_profile,'comment_count': comment_count})
@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Increment the view count
    post.views += 1
    post.save()
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        parent_id = request.POST.get('parent_id')
        if comment_text:
            new_comment = Comment(
                post=post,
                user=request.user,
                text=comment_text,
                parent_id=parent_id if parent_id else None
            )
            new_comment.save()
            return redirect('post_detail', post_id=post.id)

    comments = Comment.objects.filter(post=post, parent=None).prefetch_related('replies')
    comment_count = Comment.objects.filter(post=post).count()
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    return render(request, 'post_detail.html', {'post': post, 'user_profile': user_profile, 'comments': comments, 'comment_count': comment_count})




@login_required
def comment_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # i add these 2 myself
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        if comment_text:
            comment = Comment.objects.create(
                post=post,
                user=request.user.username,
                text=comment_text
            )
            return redirect('post_detail', post_id=post.id)

    return render(request, 'index.html', {'post': post, 'user_profile':user_profile})

@login_required
def reply_comment_view(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        if reply_text:
            reply = Comment.objects.create(
                post=post,
                user=request.user.username,
                text=reply_text,
                parent=comment
            )
            return redirect('post_detail', post_id=post.id)

    return render(request, 'index.html', {'post': post, 'comment': comment})


@login_required
def chats(request, ):

    return render(request, 'chats.html',)


# notifications

logger = logging.getLogger(__name__)

def new_like_notification(request, post_id):
    liker = request.user
    try:
        post = get_object_or_404(Post, pk=post_id)
    except Post.DoesNotExist:
        logger.error(f"The post does not exist: {post_id}")
        return render(request, 'index.html')

    try:
        notification = Notification.objects.create(
            notification_type="new_like",
            post=post,
            recipient=post.author,
            sender=liker,
        )
        notification.save()
        logger.info(f"New like notification created: {notification}")
    except Exception as e:
        logger.error(f"Error creating new like notification: {e}")
        return render(request, 'index.html')

    return render(request, 'index.html', {'notification': notification})

def new_comment_notification(request, post_id, comment_id):
    commenter = request.user
    try:
        post = get_object_or_404(Post, pk=post_id)
        comment = get_object_or_404(Comment, pk=comment_id)
    except (Post.DoesNotExist, Comment.DoesNotExist) as e:
        logger.error(f"Error getting post or comment: {e}")
        return render(request, 'index.html')

    try:
        notification = Notification.objects.create(
            notification_type="new_comment",
            post=post,
            comment=comment,
            recipient=post.author,
            sender=commenter,
        )
        notification.save()
        logger.info(f"New comment notification created: {notification}")
    except Exception as e:
        logger.error(f"Error creating new comment notification: {e}")
        return render(request, 'index.html')

    return render(request, 'index.html', {'notification': notification})

def new_reply_notification(request, comment_id, reply_id):
    replier = request.user
    try:
        comment = get_object_or_404(Comment, pk=comment_id)
        reply = get_object_or_404(Comment, pk=reply_id)
    except (Comment.DoesNotExist, Comment.DoesNotExist) as e:
        logger.error(f"Error getting comment or reply: {e}")
        return render(request, 'index.html')

    try:
        notification = Notification.objects.create(
            notification_type="new_reply",
            comment=comment,
            reply=reply,
            recipient=comment.author,
            sender=replier,
        )
        notification.save()
        logger.info(f"New reply notification created: {notification}")
    except Exception as e:
        logger.error(f"Error creating new reply notification: {e}")
        return render(request, 'index.html')

    return render(request, 'index.html', {'notification': notification})


def new_post_notification(request, post_id):
    try:
        post = get_object_or_404(Post, pk=post_id)
    except Post.DoesNotExist:
        logger.error(f"The post does not exist: {post_id}")
        return render(request, 'index.html')

    notifications = []
    for follower in post.author.followers.all():
        try:
            notification = Notification.objects.create(
                notification_type="new_post",
                post=post,
                recipient=follower,
                sender=post.author,
            )
            notification.save()
            notifications.append(notification)
            logger.info(f"New post notification created for follower: {follower}")
        except Exception as e:
            logger.error(f"Error creating new post notification for follower {follower.id}: {e}")

    return render(request, 'index.html', {'notifications': notifications})




# def chat_view(request, username):
#     current_user = request.user
#     recipient = get_object_or_404(User, username=username)

#     messages = ChatMessage.objects.filter(
#         (Q(sender_id=current_user.id) & Q(user_id=recipient.id)) |
#         (Q(sender_id=recipient.id) & Q(user_id=current_user.id))
#     ).order_by('timestamp')

#     context = {
#         'recipient': recipient,
#         'messages': messages,
#     }
#     return render(request, 'chats.html', context)
@login_required
def chat_view(request, recipient_username=None):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient_username')
        recipient = User.objects.get(username=recipient_username)
        message = request.POST['message']
        ChatMessage.objects.create(
            user=request.user,
            recipient=recipient,
            message=message,
            sender_id=request.user.id
        )
        # Mark the message as read for the recipient
        ChatMessage.objects.filter(
            user=recipient, recipient=request.user, is_read=False
        ).update(is_read=True)
        return redirect('private_chat', recipient_username=recipient_username)
    
    # Retrieve the list of online users
    # live_user_threshold = datetime.now() - timedelta(minutes=5)
    # live_users = User.objects.filter(last_login__gte=live_user_threshold)

    if recipient_username:
        recipient = get_object_or_404(User, username=recipient_username)
        messages = ChatMessage.objects.filter(
            Q(user=request.user, recipient=recipient) |
            Q(user=recipient, recipient=request.user)
        ).order_by('timestamp')
        profile = Profile.objects.get(id_user=recipient.id)
    else:
        messages = ChatMessage.objects.filter(
            Q(user=request.user) | Q(recipient=request.user)
        ).order_by('timestamp')
        profile = None

    return render(request, 'chats.html', {
        'messages': messages,
        'recipient': recipient,
        'profile': profile,
        # 'live_users':live_users
    })
    
    
    
@login_required
def withdraw_funds(request):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        if amount > 0:
            user_wallet = request.user.wallet
            if user_wallet.balance >= amount:
                user_wallet.balance -= amount
                user_wallet.save()

                # Create a withdrawal transaction
                transaction = Transaction(sender=user_wallet, receiver=None, amount=amount, description='Withdrawal')
                transaction.save()

                return JsonResponse({'success': True, 'new_balance': user_wallet.balance})
            else:
                return JsonResponse({'success': False, 'error': 'Insufficient funds'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid amount'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def wallet_balance(request):
    user_wallet = request.user.wallet
    return JsonResponse({'balance': user_wallet.balance})

@login_required
def transaction_history(request):
    user_wallet = request.user.wallet
    transactions = Transaction.objects.filter(models.Q(sender=user_wallet) | models.Q(receiver=user_wallet)).order_by('-timestamp')
    transaction_data = [
        {
            'id': t.id,
            'sender': t.sender.user.username if t.sender else 'System',
            'receiver': t.receiver.user.username if t.receiver else 'System',
            'amount': t.amount,
            'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'description': t.description
        } for t in transactions
    ]
    return JsonResponse({'transactions': transaction_data})
    
@login_required
def transfer_money(request):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient_username')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')

        if not recipient_username or not amount:
            messages.error(request, 'Recipient username and amount are required.')
            return redirect('wallet_balance')

        try:
            amount = float(amount)
            recipient = User.objects.get(username=recipient_username)
            sender_wallet = request.user.wallet
            recipient_wallet = recipient.wallet

            if sender_wallet.balance >= amount:
                sender_wallet.balance -= amount
                recipient_wallet.balance += amount
                sender_wallet.save()
                recipient_wallet.save()

                # Create a transaction record
                Transaction.objects.create(
                    sender=sender_wallet,
                    receiver=recipient_wallet,
                    amount=amount,
                    description=description
                )

                messages.success(request, f'Successfully transferred ${amount} to {recipient_username}.')
            else:
                messages.error(request, 'Insufficient balance to complete the transaction.')
        except User.DoesNotExist:
            messages.error(request, 'Recipient user does not exist.')
        except ValueError:
            messages.error(request, 'Invalid amount.')
        return redirect('wallet_balance')
    return redirect('wallet_balance')
    
    
    
    