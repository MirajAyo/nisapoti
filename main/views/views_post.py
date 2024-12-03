
from django.views.decorators.csrf import csrf_exempt
from django.http import  JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from ..models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash


from django.contrib.auth.models import User, auth
# from .forms import CartForm



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



# def post_detail(request, post_id):
#     post = Post.objects.get(id=post_id)  # Get the specific post
#     return render(request, 'index.html', {'post': post})


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

    
    
