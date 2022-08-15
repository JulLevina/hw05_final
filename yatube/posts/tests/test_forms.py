import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from faker import Faker

from ..models import Comment, Group, Post

User = get_user_model()

settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password()
        )
        cls.user_author = User.objects.create_user(
            username=fake.user_name(),
            password=fake.password()
        )
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text()
        )
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text=fake.text(),
            group=cls.group,
        )
        small_gif = fake.image()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(
            PostCreateFormTests.user_author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        fake = Faker()
        posts_count = Post.objects.count()
        test_text = fake.text()
        form_data = {
            'text': test_text,
            'group': PostCreateFormTests.group.pk,
            'image': PostCreateFormTests.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=(PostCreateFormTests.user,)))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        expcted_value = 'page_obj'
        self.assertIn(expcted_value, response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, test_text)
        self.assertEqual(first_post.group, PostCreateFormTests.group)
        self.assertEqual(first_post.author, PostCreateFormTests.user)
        self.assertTrue(first_post.image)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        fake = Faker()
        new_group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
        )
        test_post = Post.objects.create(
            author=PostCreateFormTests.user,
            text=fake.text(),
            group=new_group,
        )
        posts_count = Post.objects.count()
        test_text = fake.text()
        form_data = {
            'text': test_text,
            'group': new_group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    args=(test_post.id,)),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(test_post.id,)))
        test_post.refresh_from_db()
        self.assertEqual(test_post.text,
                         test_text)
        self.assertEqual(test_post.group, new_group)
        self.assertEqual(test_post.author, PostCreateFormTests.user)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_by_author(self):
        """Валидная форма не редактирует запись в Post,
        авторизованный пользователь, не являющйся автором поста,
        перенаправляется на страницу просмотра поста."""
        fake = Faker()
        new_group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
        )
        test_post = Post.objects.create(
            author=PostCreateFormTests.user_author,
            text=fake.text(),
            group=new_group
        )
        form_data = {
            'text': test_post.text,
            'group': new_group
        }
        self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        posts_count = Post.objects.count()
        response = self.authorized_client.post(reverse(
            'posts:post_edit',
            args=(test_post.pk,)),
            data=form_data,
            follow=True)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(test_post.pk,)),
        )

    def test_comment_create(self):
        """Валидная форма создает комментарии к записям,
        отображаемым на странице поста."""
        fake = Faker()
        comments_count = Comment.objects.count()
        form_comment_data = {
            'text': fake.text(),
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    args=(PostCreateFormTests.post_1.pk,)
                    ),
            data=form_comment_data,
            follow=True)
        page_with_comment = reverse('posts:post_detail',
                                    args=(PostCreateFormTests.post_1.pk,))
        self.assertRedirects(response, page_with_comment)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        expcted_value = 'comments'
        self.assertIn(expcted_value, response.context)
        first_comment = response.context['comments'][0]
        self.assertEqual(first_comment.text, form_comment_data['text'])
        self.assertEqual(first_comment.post, PostCreateFormTests.post_1)
        self.assertEqual(first_comment.author, PostCreateFormTests.user)


class GuestPostCreateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name()
        )
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text()
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text(),
            group=cls.group,
        )

    def test_create_post_by_guest_client(self):
        """Валидная форма создания поста перенаправляет
        неавторизованного пользователя на страницу авторизации."""
        posts_count = Post.objects.count()
        form_data = {
            'text': GuestPostCreateFormTests.post.text,
            'group': GuestPostCreateFormTests.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        login = reverse('login')
        new_post = reverse('posts:post_create')
        redirect = login + '?next=' + new_post
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_comment_create_by_guest(self):
        """Валидная форма создания комментария возвращает
        неавторизованного пользователя на страницу просмотра поста."""
        fake = Faker()
        comments_count = Comment.objects.count()
        form_comment_data = {
            'text': fake.text(),
        }
        response = self.client.post(
            reverse('posts:add_comment',
                    args=(GuestPostCreateFormTests.post.pk,)
                    ),
            data=form_comment_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        login = reverse('login')
        page_without_comment = reverse('posts:add_comment',
                                       args=(GuestPostCreateFormTests.post.pk,)
                                       )
        page_redirect = login + '?next=' + page_without_comment
        self.assertRedirects(response, page_redirect)
        self.assertEqual(Comment.objects.count(), comments_count)
