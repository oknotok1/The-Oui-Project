from .serializers import *
from .models import *
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post
import os

# Create your tests here.


class PostTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.post = Post.objects.create(
            user=self.user, caption='Test caption')
        self.client.login(username='testuser', password='testpassword')

    def test_index_view(self):
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertInHTML(self.post.caption, response.content.decode())

    def test_create_post_with_image(self):
        # Test that a new post can be created with an image
        self.client.login(username='testuser', password='testpassword')
        image_path = 'static/images/banner.jpg'
        if os.path.exists(image_path):
            with open(image_path, 'rb') as fp:
                response = self.client.post(reverse('upload'), {
                    'caption': 'Test post with image',
                    'image_upload': fp,
                })

            # check that the response is a redirect
            self.assertEqual(response.status_code, 302)

            # check that the new post was created
            self.assertEqual(Post.objects.count(), 2)
        else:
            print('ERROR: Image file not found')


class ProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='testpass')
        self.profile = Profile.objects.create(
            user=self.user, id_user=self.user.id, bio='Test bio', location='Test location')

    def test_profile_list(self):
        url = reverse('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_profile_detail(self):
        username = self.user1.username
        url = reverse('profile-detail', kwargs={'username': username})
        response = self.client.get(url)
        print(response.status_code)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], username)

    def test_profile_create(self):
        self.client.login(username='testuser', password='testpass')
        data = {'user': self.user.id, 'bio': 'Test bio',
                'location': 'Test location'}
        url = reverse('signup')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, '/settings/')
        profile = Profile.objects.get(user=self.user)
        serializer = ProfileSerializer(profile)
        self.assertEqual(serializer.data['bio'], 'Test bio')
        self.assertEqual(serializer.data['location'], 'Test location')

    def test_profile_update(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('profile-detail',
                      kwargs={'username': self.user.username})
        data = {'bio': 'Updated bio', 'location': 'Updated location'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=self.user)
        serializer = ProfileSerializer(profile)
        self.assertEqual(response.data, serializer.data)
