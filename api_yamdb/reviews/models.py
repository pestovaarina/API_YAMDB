from enum import Enum
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_username

Limit_on_the_number_of_characters = 30


class Role(Enum):
    USER = 'user', 'Аутентифицированный пользователь'
    MODERATOR = 'moderator', 'Модератор'
    ADMIN = 'admin', 'Администратор'


class User(AbstractUser):
    """Кастомная модель пользователя."""

    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[validate_username])
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=True)
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=True)
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
        blank=False)
    bio = models.TextField(
        'Биография',
        blank=True,)
    role = models.CharField(
        'Роль',
        max_length=150,
        choices=[(role.value[0], role.value[1]) for role in Role],
        default=Role.USER.value[0]
    )
    confirmation_code = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Код для идентификации'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        """Пользователь с правами администратора."""
        return (self.role == Role.ADMIN.value[0]
                or self.is_staff
                or self.is_superuser)

    @property
    def is_moderator(self):
        """Пользователь с правами модератора."""
        return self.role == Role.MODERATOR.value[0]

    @property
    def is_user(self):
        """Обычный пользователь."""
        return self.role == Role.USER.value[0]

    def __str__(self):
        return self.username


class Category(models.Model):
    """Модель 'Категории'."""
    name = models.CharField(
        max_length=200,
        verbose_name='Категория')
    slug = models.SlugField(
        max_length=50,
        unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель 'Жанры'."""
    name = models.CharField(
        max_length=256,
        verbose_name='Жанр')
    slug = models.SlugField(
        max_length=50,
        unique=True)

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель 'Произведения'.

    В поле genre явно указал параметр through='GenreTitle'(Модель-посредник),
    чтобы указать модель GenreTitle - представляющую промежуточную таблицу.
    """
    name = models.CharField(
        max_length=256,
        verbose_name='Название')
    year = models.IntegerField(
        verbose_name='Год выпуска')
    description = models.TextField(
        verbose_name='Описание')
    genre = models.ManyToManyField(
        Genre,
        blank=True,
        related_name='titles',
        through='GenreTitle',
        verbose_name='Slug жанра')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='titles',
        verbose_name='Slug категории')

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
    """Модель-посредник.

    Явно указаны внешние ключи для моделей Genres и Titles,
    которые участвуют в отношениях ManyToMany.
    """
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Жанр')
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение')

    def __str__(self):
        return f'{self.title} - {self.genre}'


class Review(models.Model):
    """Модель 'Отзывы'.
    """
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение',
        null=True)
    text = models.TextField(
        verbose_name='Текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор')
    score = models.IntegerField(
        validators=[MinValueValidator(0),
                    MaxValueValidator(10)],
        verbose_name='Ваша оценка')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации')

    def __str__(self):
        return self.text[:Limit_on_the_number_of_characters]

    class Meta:
        ordering = ["-pub_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["author", "title"],
                name="unique_review"
            )
        ]


class Comment(models.Model):
    """Модель 'Коментарии'."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв')
    text = models.TextField(
        verbose_name='Текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата добавления')

    def __str__(self):
        return self.text
