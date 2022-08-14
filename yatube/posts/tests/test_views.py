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
        Post.objects.bulk_create(objs)

    def setUp(self):
        cache.clear()

    def test_page_contains_expected_value_of_records(self):
        pages_list = {
            1: settings.NUMBER_OF_POSTS,
            2: self.number_of_posts - settings.NUMBER_OF_POSTS,
        }
        for page, post_number in pages_list.items():
            with self.subTest(page=page):
                context = {
                    reverse('posts:index'),
                    reverse('posts:group_posts',
                            args=(PaginatorViewsTest.group.slug,)),
                    reverse('posts:profile',
                            args=(PaginatorViewsTest.user,)),
                }
                for reverse_name in context:
                    with self.subTest():
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
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
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
            PostPagesTests.post: first_post,
            PostPagesTests.group: first_post.group,
            PostPagesTests.post.image: first_post.image,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts.html сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:group_posts', args=(PostPagesTests.group.slug,)))
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(response.context['group'], PostPagesTests.group)
        self.assertEqual(first_post, PostPagesTests.post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:profile', args=(PostPagesTests.user,)))
        self.assertIn('page_obj', response.context)
        self.assertIn('author', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(response.context['author'], PostPagesTests.user)
        self.assertEqual(first_post, PostPagesTests.post)

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
        url_context = (
            reverse('posts:index'),
            reverse('posts:group_posts', args=(PostPagesTests.group.slug,)),
            reverse('posts:profile', args=(PostPagesTests.user,)),
            reverse('posts:post_detail', args=(PostPagesTests.post.pk,)),
        )
        for reverse_name in url_context:
            with self.subTest():
                self.client.get(reverse_name)
                self.assertEqual(PostPagesTests.post.image, 'posts/small.gif')


class CasheIndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name())

    def test_cache_index_page(self):
        test_post = Post.objects.create(author=CasheIndexTests.user)
        response = self.client.get(reverse('posts:index'))
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
        self.authorized_follower = Client()
        self.authorized_follower.force_login(FollowTests.follower)
        self.authorized_follower_2 = Client()
        self.authorized_follower_2.force_login(FollowTests.follower_2)
        self.authorized_following = Client()
        self.authorized_following.force_login(FollowTests.following)

    def test_follow_self(self):
        """Проверяем, что нельзя подписаться на самого себя."""
        fake = Faker()
        new_following = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password())
        authorized_new_following = Client()
        authorized_new_following.force_login(new_following)
        self.assertFalse(Follow.objects.filter(
            user=new_following,
            author=new_following
        ).exists()
        )
        response = authorized_new_following.get(reverse(
            'posts:profile_follow',
            args=(new_following.username,)),
            follow=True)
        self.assertRedirects(response, (reverse(
            'posts:profile', args=(new_following.username,))))
        self.assertFalse(Follow.objects.filter(
            user=new_following,
            author=new_following,
        ).exists()
        )

    def test_follow(self):
        """Проверяем, что авторизованный пользователь
        может подписываться на других пользователей."""
        fake = Faker()
        follows = Follow.objects.count()
        new_following = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password()
        )
        response = self.authorized_follower.get(reverse(
            'posts:profile_follow',
            args=(new_following.username,)),
            follow=True)
        author_profile = reverse(
            'posts:profile',
            args=(new_following.username,)
        )
        self.assertRedirects(response, author_profile)
        self.assertEqual(follows + 1, 1)
        self.assertTrue(Follow.objects.filter(
            user=FollowTests.follower,
            author=new_following,
        ).exists()
        )

    def test_unfollow(self):
        """Проверяем, что авторизованный пользователь
        может отписываться от авторов."""
        fake = Faker()
        new_following = User.objects.create(
            username=fake.user_name(),
            password=fake.password())
        Follow.objects.create(
            user=FollowTests.follower,
            author=new_following
        )
        follows = Follow.objects.count()
        self.assertEqual(follows, 1)
        response = self.authorized_follower.get(reverse(
            'posts:profile_unfollow', args=(new_following.username,)),
            follow=True)
        author_profile = reverse(
            'posts:profile',
            args=(new_following.username,))
        self.assertEqual(follows - 1, 0)
        self.assertRedirects(
            response, author_profile)
        self.assertFalse(Follow.objects.filter(
            user=FollowTests.follower,
            author=new_following,
        ).exists()
        )

    def test_re_subscribing(self):
        """Проверяем невозможность подписки
        на одного и того же автора."""
        fake = Faker()
        follows = Follow.objects.count()
        new_following = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password())
        self.assertFalse(Follow.objects.filter(
            user=FollowTests.follower,
            author=new_following,
        ).exists()
        )
        self.authorized_follower.get(reverse(
            'posts:profile_follow', args=(new_following.username,)),
            follow=True)
        self.assertEqual(follows + 1, 1)
        self.authorized_follower.get(reverse(
            'posts:profile_follow', args=(new_following.username,)),
            follow=True)
        self.assertEqual(follows + 1, 1)

    def test_profile_follow(self):
        """Проверяем, что новый пост автора появляется только у подписчика."""
        fake = Faker()
        new_following = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password()
        )
        Follow.objects.create(
            user=FollowTests.follower,
            author=new_following
        )
        self.assertEqual(Follow.objects.count(), 1)
        test_post = Post.objects.create(
            text=fake.text(),
            author=new_following)
        response = self.authorized_follower.get(
            reverse('posts:follow_index'))
        all_posts = response.context['page_obj']
        self.assertIn(test_post, all_posts)
        response = self.authorized_follower_2.get(
            reverse('posts:follow_index'))
        all_posts = response.context['page_obj']
        self.assertNotIn(test_post, all_posts)
