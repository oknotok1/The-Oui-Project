from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from requests import Response
from .models import Profile, Post, LikePost, FollowersCount
from itertools import chain
import random


# API imports
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from .models import Profile
from .serializers import ProfileSerializer

from .serializers import ProfileSerializer
from .models import Profile


# Create your views here.


@login_required(login_url='login')
def index(request):
    try:
        # Ensure that logged in user has a profile
        user_object = User.objects.get(username=request.user)
        user_profile = Profile.objects.get(user=user_object)
    except Profile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        # messages.warning(request, "Account does not exist. Please sign up, or enter a valid username and password.")
        logout(request)
        return redirect('login')

    # To get the posts of the users that the logged in user is following
    user_following_list = []
    following_feed = []

    user_following = FollowersCount.objects.filter(
        follower=request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        following_feed.append(feed_lists)

    # To get the user's own posts
    user_posts = Post.objects.filter(user=request.user.username)

    feed = list(chain(*following_feed)) + list(user_posts)

    # Add profile image URLs to each post
    for post in feed:
        profile = Profile.objects.get(user__username=post.user)
        post.profile_img_url = profile.profile_img.url

    # To show all posts in the database
    # posts = Post.objects.all().order_by('-created_at')
    # posts = Post.objects.all()

    # User stats
    user_posts = Post.objects.filter(user=request.user)
    user_post_count = len(user_posts)
    user_follower_count = len(FollowersCount.objects.filter(
        user=request.user))
    user_following_count = len(FollowersCount.objects.filter(
        follower=request.user))

    # Suggested users to follow
    all_users = User.objects.all()

    # Get a list of usernames that the current user is already following
    following_usernames = [follow.user for follow in user_following]

    # Filter out the current user and those already being followed
    suggested_users = all_users.exclude(
        username=request.user.username).exclude(
        username__in=following_usernames)

    # Shuffle the list of suggested users
    suggested_users = list(suggested_users)
    random.shuffle(suggested_users)

    # Get the profiles of the suggested users
    suggested_users_profiles = Profile.objects.filter(user__in=suggested_users)

    context = {
        'user_profile': user_profile,
        'posts': feed,
        'suggested_users': suggested_users_profiles,
        'user_post_count': user_post_count,
        'user_following_count': user_following_count,
        'user_follower_count': user_follower_count,
    }

    return render(request, 'index.html', context)


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email taken")
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username taken")
                return redirect('signup')
            else:
                user = User.objects.create_user(
                    username=username, email=email, password=password)
                user.save()

                # log user in and redirect to settings page
                user_login = auth.authenticate(
                    username=username, password=password)
                auth.login(request, user_login)

                # create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(
                    user=user_model, id_user=user_model.id)
                new_profile.save()
                # return redirect('signin')
                return redirect('settings')

        else:
            messages.info(request, "Passwords do not match")
            return redirect('signup')

    else:
        return render(request, 'signup.html')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, "Invalid credentials")
            return redirect('login')

    return render(request, 'login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')


@login_required(login_url='login')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        if request.FILES.get('image') == None:
            image = user_profile.profile_img
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profile_img = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()

        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profile_img = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()

        messages.info(request, "Updates saved!")
        return redirect('settings')

    return render(request, 'settings.html', {'user_profile': user_profile})


@login_required(login_url='login')
def profile(request, pk):
    current_user = Profile.objects.get(user=request.user)
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_len = len(user_posts)

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_follower_len = len(FollowersCount.objects.filter(user=pk))
    user_following_len = len(FollowersCount.objects.filter(follower=pk))

    context = {
        'current_user': current_user,
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_len': user_post_len,
        'user_follower_len': user_follower_len,
        'user_following_len': user_following_len,
        'button_text': button_text,
        'profile_img_url': user_profile.profile_img.url,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='login')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        # Unfollow
        if FollowersCount.objects.filter(follower=follower, user=user).exists():
            remove_follower = FollowersCount.objects.get(
                follower=follower, user=user)
            remove_follower.delete()
            return redirect('/profile/' + user)
        # Follow
        else:
            add_follower = FollowersCount.objects.create(
                follower=follower, user=user)
            add_follower.save()
            return redirect('/profile/' + user)

    else:
        return redirect('/')


@login_required(login_url='login')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        # username = request.POST['username']
        username = request.POST.get('username')
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        search_results = list(chain(*username_profile_list))

    # User stats
    user_posts = Post.objects.filter(user=request.user)
    user_post_count = len(user_posts)
    user_follower_count = len(FollowersCount.objects.filter(
        user=request.user))
    user_following_count = len(FollowersCount.objects.filter(
        follower=request.user))

    # Suggested users to follow
    all_users = User.objects.all()

    # Get a list of usernames that the current user is already following
    user_following = FollowersCount.objects.filter(
        follower=request.user.username)
    following_usernames = [follow.user for follow in user_following]

    # Filter out the current user and those already being followed
    suggested_users = all_users.exclude(
        username=request.user.username).exclude(
        username__in=following_usernames)

    # Shuffle the list of suggested users
    suggested_users = list(suggested_users)
    random.shuffle(suggested_users)

    # Get the profiles of the suggested users
    suggested_users_profiles = Profile.objects.filter(user__in=suggested_users)

    context = {
        "user_profile": user_profile,
        'user_post_count': user_post_count,
        'user_following_count': user_following_count,
        'user_follower_count': user_follower_count,
        'suggested_users': suggested_users_profiles,
        "searched_user": username,
        'search_results': search_results
    }

    return render(request, 'search.html', context)


@ login_required(login_url='login')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        return redirect('/')

    else:
        return redirect('/')


@ login_required(login_url='login')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    # check if post has already been liked if post exists
    check_post_like = LikePost.objects.filter(
        post_id=post_id, username=username).first()

    if check_post_like == None:
        new_like = LikePost.objects.create(
            post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes += 1
        post.save()
        return redirect('/')

    else:
        check_post_like.delete()
        post.no_of_likes -= 1
        post.save()
        return redirect('/')


# API Views

class ProfileList(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProfileDetail(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        username = self.kwargs.get('username')
        profile = get_object_or_404(Profile, user__username=username)
        return profile
