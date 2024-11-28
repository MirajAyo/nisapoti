from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

User = get_user_model()

# Create your models here.

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    RELATIONSHIP_CHOICES = [
        ('S', 'Single'),
        ('R', 'In a relationship'),
        ('C', 'Complicated'),
        ('M', 'Married'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    bio = models.TextField(blank=True)
    profileimg = models.ImageField(upload_to='profile_images', default='default.jpg')
    location = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    relationship_status = models.CharField(max_length=1, choices=RELATIONSHIP_CHOICES, blank=True)

    def __str__(self):
        return self.user.username
    
    
    
class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.CharField(max_length=100)
    image = models.ImageField(upload_to='post_images', blank=True, null=True)  # Optional
    caption = models.TextField(blank=True, null=True)  # Optional
    created_at = models.DateTimeField(auto_now_add=True)
    no_of_likes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.user


    
class LikePost(models.Model):
    post_id=models.CharField(max_length=500)
    username=models.CharField(max_length=100)

    def __str__(self):
        return self.username


class FollowersCount(models.Model):
    follower=models.CharField(max_length=100)
    user=models.CharField(max_length=100)

    def __str__(self):
        return self.user
    

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_follower', 'New Follower'),
        ('new_post', 'New Post'),
        ('new_comment', 'New Comment'),
        ('new_reply', 'New Reply'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sender.username} - {self.get_notification_type_display()}"
    



class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    sender_id = models.IntegerField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} to {self.recipient.username}: {self.message}"
        
        
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

class Transaction(models.Model):
    sender = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Transaction from {self.sender.user.username} to {self.receiver.user.username}"
