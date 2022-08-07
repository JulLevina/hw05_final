import shutil
import tempfile
from random import randint

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from faker import Faker

from ..models import Follow, Group, Post
from ..forms import PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name())
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),
        )
        cls.number_of_posts = randint(settings.NUMBER_OF_POSTS + 1,
                                      settings.NUMBER_OF_POSTS * 2)

        objs = [
            Post(
                author=PaginatorViewsTest.user,
                text=fake.text(),
                group=PaginatorViewsTest.group
            )
            for _ in range(PaginatorViewsTest.number_of_posts)
        ]
        cls.post = Post.objects.bulk_create(objs)

    def test_page_contains_expected_value_of_records(self):
        cache.clear()
        context = {
            reverse('posts:index'),
            reverse('posts:group_posts',
                    args=(PaginatorViewsTest.group.slug,)),
            reverse('posts:profile',
                    args=(PaginatorViewsTest.user,)),
        }
        for reverse_name in context:
            with self.subTest():
                pages_list = {
                    1: settings.NUMBER_OF_POSTS,
                    2: self.number_of_posts - settings.NUMBER_OF_POSTS,
                }
                for page, post_number in pages_list.items():
                    with self.subTest(page=page):
                        response = self.client.get(reverse_name,
                                                   {'page': page})
                        self.assertEqual(len(response.context['page_obj']),
                                         post_number)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        small_gif = fake.image()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(
            username=fake.user_name())
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text(),
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def test_pages_show_correct_context(self):
        """Шаблоны отображаемых страниц сформированы
        с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        expcted_value = 'page_obj'
        self.assertIn(expcted_value, response.context)
        first_post = response.context['page_obj'][0]
        context_objects = {
            PostPagesTests.user: first_post.author,
            PostPagesTests.post.text: first_post.text,
            PostPagesTests.group: first_post.group,
            PostPagesTests.post.image: first_post.image,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)
                cache.clear()

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts.html сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:group_posts', args=(PostPagesTests.group.slug,)))
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(response.context['group'], PostPagesTests.group)
        self.assertEqual(first_post, Post.objects.first())

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:profile', args=(PostPagesTests.user,)))
        self.assertIn('page_obj', response.context)
        self.assertIn('author', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(response.context['author'], PostPagesTests.user)
        self.assertEqual(first_post, Post.objects.first())

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:post_detail', args=(PostPagesTests.post.pk,)))
        self.assertIn('user_post', response.context)
        self.assertEqual(response.context['user_post'],
                         PostPagesTests.post)

    def test_image_correct_show(self):
        """Изображение передается в шаблон
        главной страницы, страницу профиля, группы, поста."""
        url_context = {
            reverse('posts:index'),
            reverse('posts:group_posts', args=(PostPagesTests.group.slug,)),
            reverse('posts:profile', args=(PostPagesTests.user,)),
            reverse('posts:post_detail', args=(PostPagesTests.post.pk,))
        }
        for url in url_context:
            with self.subTest():
                response = self.client.get(url)
                self.assertIn('image', response.content.decode())


class CasheIndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name())
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text(),
            group=cls.group,
        )

    def test_cache_index_page(self):
        test_post = Post.objects.create(author=CasheIndexTests.user)
        response = self.client.get(reverse('posts:index'))
        Post.objects.filter(pk=test_post.pk)
        test_post.delete()
        response_2 = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_3.content)


class PostPagesTestsForUsers(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password())
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text(),
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTestsForUsers.user)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create.html для создания поста
        сформирован с правильным контекстом."""
        expected_values = {
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    args=(PostPagesTestsForUsers.post.pk,)),
        }
        for reverse_name in expected_values:
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                form = response.context['form']
                self.assertIsInstance(form, PostForm)
                if 'is_edit' in response.context:
                    self.assertIn('is_edit', response.context)


class FollowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.follower = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password())
        cls.follower_2 = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password())
        cls.following = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password())
        cls.post = Post.objects.create(
            author=cls.following,
            text=fake.text(),
        )

    def setUp(self):
        self.follower = Client()
        self.follower.force_login(FollowTests.follower)
        self.follower_2 = Client()
        self.follower_2.force_login(FollowTests.follower_2)
        self.following = Client()
        self.following.force_login(FollowTests.following)

    def test_follow_self(self):
        """Проверяем, что нельзя подписаться на самого себя."""
        self.follower.get(reverse(
            'posts:profile_follow', args=(FollowTests.follower,)),
            follow=True)
        self.assertFalse(Follow.objects.filter(
            user=FollowTests.follower,
            author=FollowTests.follower,
        ).exists()
        )

    def test_follow(self):
        """Проверяем, что авторизованный пользователь
        может подписываться на других пользователей."""
        self.follower.get(reverse(
            'posts:profile_follow', args=(FollowTests.following,)),
            follow=True)
        self.assertEqual(Follow.objects.all().count(), 1)
        self.assertTrue(Follow.objects.filter(
            user=FollowTests.follower,
            author=FollowTests.following,
        ).exists()
        )

    def test_unfollow(self):
        """Проверяем, что авторизованный пользователь
        может отписываться от авторов."""
        self.follower.get(reverse(
            'posts:profile_unfollow', args=(FollowTests.following,)),
            follow=True)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_profile_follow(self):
        cache.clear()
        fake = Faker()
        self.follower.get(reverse(
            'posts:profile_follow', args=(FollowTests.following,)))
        self.assertEqual(Follow.objects.count(), 1)
        form_data = {
            'text': fake.text()
        }
        self.following.post(reverse('posts:post_create'),
                            data=form_data, follow=True)
        response = self.follower.get(reverse('posts:follow_index'))
        self.assertContains(response, form_data['text'])
        response = self.follower_2.get(reverse('posts:follow_index'))
        self.assertNotContains(response, form_data['text'])
