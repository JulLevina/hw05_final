from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы')
    slug = models.SlugField(
        unique=True,
        verbose_name='slug')
    description = models.TextField(verbose_name='Описание')

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Новый пост',
        help_text='Текст нового поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        db_index=True,
        verbose_name='Автор')
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        return self.text[:settings.SHOW_POST_NUMBER_OF_CHARACTERS]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментарии',
        help_text='Ваш комментарий к записи')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор')
    text = models.TextField(
        verbose_name='Новый комментарий',
        help_text='Текст нового комментария')
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Опубликовано: ')

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        return self.text


class Follow (models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]
