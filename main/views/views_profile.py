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

#import winsound  # For Windows only, use appropriate library for your OS
from django.conf import settings
import os

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



# def profile_view(request):
#     # Redirect to the logged-in user's profile
#     return redirect('profile', pk=request.user.username)


@login_required(login_url='signin')
def follow(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        follower = data.get("follower")
        user = data.get("user")

        # Check if the follower relationship exists
        existing_follow = FollowersCount.objects.filter(follower=follower, user=user).first()

        if existing_follow:
            existing_follow.delete()
            return JsonResponse({"success": True, "following": False})  # Unfollowed
        else:
            FollowersCount.objects.create(follower=follower, user=user)
            return JsonResponse({"success": True, "following": True})  # Followed

    return JsonResponse({"success": False})


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        # Handle image upload
        if 'image' in request.FILES:
            user_profile.profileimg = request.FILES['image']
        
        # Update bio, location, gender, and relationship status
        user_profile.bio = request.POST.get('bio', '')
        user_profile.location = request.POST.get('location', '')

        # Gender and relationship status should be saved with the correct choices
        gender = request.POST.get('gender', '')
        if gender in ['M', 'F', 'O']:
            user_profile.gender = gender

        relationship_status = request.POST.get('relationship_status', '')
        if relationship_status in ['S', 'R', 'C', 'M']:
            user_profile.relationship_status = relationship_status
        
        # Update user fields: first_name, last_name, email, username
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', user.username)  # Keep the existing username if not updated
        user.save()

        # Save the profile
        user_profile.save()
        messages.success(request, 'Profile updated successfully.')

        return redirect('settings')
    else:
        return render(request, 'settings.html', {
            'user_profile': user_profile,
        })
  
  
def update_profile_image(request):
    if request.method == 'POST':
        user_profile = request.user.profile  # Assuming a OneToOne relation with Profile
        new_image = request.FILES.get('profileimg')
        
        if new_image:
            # Delete the old image if it's not the default
            if user_profile.profileimg.name != 'default.jpg':
                old_image_path = os.path.join(settings.MEDIA_ROOT, str(user_profile.profileimg))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Update with the new image
            user_profile.profileimg = new_image
            user_profile.save()
            messages.success(request, "Profile image updated successfully!")
        else:
            messages.error(request, "No image selected!")
    
    return redirect('profile_view')  # Replace with the appropriate redirect
    
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
    
    
    
    
