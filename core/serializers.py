from rest_framework import serializers
from .models import *


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'user', 'image', 'caption',
                  'created_at', 'no_of_likes')


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    num_posts = serializers.SerializerMethodField()
    posts = PostSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'id_user', 'bio', 'profile_img', 'location',
                  'user', 'follower_count', 'following_count', 'num_posts', 'posts')

    def get_follower_count(self, obj):
        return FollowersCount.objects.filter(user=obj.user.username).count()

    def get_following_count(self, obj):
        return FollowersCount.objects.filter(follower=obj.user.username).count()

    def get_num_posts(self, obj):
        return Post.objects.filter(user=obj.user.username).count()
