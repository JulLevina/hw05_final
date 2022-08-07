from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from faker import Faker

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.user = User.objects.create_user(
            username=fake.user_name())
        cls.group = Group.objects.create(
            title=fake.name(),
            slug=fake.slug(),
            description=fake.text(),)
        cls.post = Post.objects.create(
            author=cls.user,
            text=fake.text())

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает метод __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        limit = settings.SHOW_POST_NUMBER_OF_CHARACTERS
        list_of_expected_values = {
            post.text[:limit]: str(post),
            group.title: str(group),
        }
        for expected_value, method in list_of_expected_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(expected_value,
                                 method,
                                 'Метод __str__ работает некорректно!'
                                 )

    def test_models_have_correct_verbose_names(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Новый пост',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_models_have_correct_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
