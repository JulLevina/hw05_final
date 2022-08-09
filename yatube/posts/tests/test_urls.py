from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from faker import Faker

from ..models import Group, Post

User = get_user_model()


class PostUserURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password(),
        )
        cls.user_2 = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password(),
        )
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text(),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUserURLTests.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(PostUserURLTests.user_2)

    def test_urls_for_users_show_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names_for_users = {
            reverse(
                'posts:post_create'):
                    'posts/post_create.html',
            reverse(
                'posts:post_edit',
                args=(PostUserURLTests.post.pk,)):
                    'posts/post_create.html',
            reverse('posts:follow_index'):
                'posts/follow.html',
        }

        for reverse_name, template in url_templates_names_for_users.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_url_for_users(self):
        """Страницы, доступные авторизованному пользователю,
        являющемуся автором поста."""
        url_pages_list = (
            reverse(
                'posts:post_create'),
            reverse(
                'posts:post_edit',
                args=(PostUserURLTests.post.pk,)),
            reverse('posts:follow_index'),
        )
        for reverse_name in url_pages_list:
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_for_authorized_user_not_author(self):
        """Страница редактирования поста '/posts/<post_id>/edit/'
        не доступна для авторизованного пользователя,
        не являющегося автором поста."""
        response = self.authorized_client_2.get(
            reverse('posts:post_edit',
                    args=(PostUserURLTests.post.pk,)))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class PostGuestURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name()
        )
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text(),
        )

    def setUp(self):
        cache.clear()

    def test_urls_for_guest_show_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names_for_guests = {
            reverse('posts:index'):
            'posts/index.html',
            reverse(
                'posts:group_posts',
                args=(PostGuestURLTests.group.slug,)):
            'posts/group_list.html',
            reverse(
                'posts:profile',
                args=(PostGuestURLTests.user,)):
            'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=(PostGuestURLTests.post.pk,)):
            'posts/post_detail.html',
        }
        for reverse_name, template in url_templates_names_for_guests.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_url_for_guests(self):
        """Страницы, доступные любому пользователю."""
        url_pages_list = (
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                args=(PostGuestURLTests.group.slug,)),
            reverse(
                'posts:profile',
                args=(PostGuestURLTests.user,)),
            reverse(
                'posts:post_detail',
                args=(PostGuestURLTests.post.pk,)),
        )
        for reverse_name in url_pages_list:
            with self.subTest():
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_unauthorized_user_on_login(self):
        """Cтраницы по адресу '/create/', '/posts/<post_id>/edit/',
        '/follow/'перенаправят неавторизованного пользователя на страницу
        авторизации.
        """
        url_addresses = (
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': PostGuestURLTests.post.pk}),
            reverse('posts:follow_index'),
            reverse('posts:profile_follow',
                    args=(PostGuestURLTests.user,)),
            reverse('posts:profile_unfollow',
                    args=(PostGuestURLTests.user,)),
        )
        for address in url_addresses:
            with self.subTest():
                response = self.client.get(address, follow=True)
                login = reverse('users:login')
                self.assertRedirects(
                    response, f'{login}?next={address}')

    def test_unexisting_page_url_get_404(self):
        """Страница '/unexisting_page/' не существует: код ошибки 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_404(self):
        """Код ошибки 404 возвращает кастомный шаблон."""
        response = self.client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
