from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('settings', views.settings, name='settings'),
    path('profile/<str:pk>', views.profile, name='profile'),
    path('follow', views.follow, name='follow'),
    path('search', views.search, name='search'),
    path('upload', views.upload, name='upload'),
    path('like-post', views.like_post, name='like-post'),

    # API Routes
    path('profiles', ProfileList.as_view()),
    path('profiles/<str:username>', ProfileDetail.as_view()),
]
