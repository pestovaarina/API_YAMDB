from datetime import date

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from reviews.models import (Category, Comment, Genre, GenreTitle, Review,
                            Title, User)
from reviews.validators import validate_username


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели User."""
    class Meta:
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role',)
        model = User


class SignupSerializer(serializers.Serializer):
    """Сериализация данных пользователя при регистрации."""
    email = serializers.EmailField(required=True, max_length=254)
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[validate_username]
    )


class TokenSerializer(serializers.Serializer):
    """Сериализация данных для получения токена."""
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[validate_username]
    )
    confirmation_code = serializers.CharField(required=True, max_length=150)


class CategoriesSerializer(serializers.ModelSerializer):
    """Сериализатор модели Categories."""
    class Meta:
        fields = ('name', 'slug')
        model = Category


class GenresSerializer(serializers.ModelSerializer):
    """Сериализатор модели Genres."""
    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitlesSerializer(serializers.ModelSerializer):
    """Сериализатор для получения обьектов Titles.

    Обрабатывет:
    GET-запросы для получения списка объектов Title.
    GET-запросы для получения конкретного объекта Title по его id.
    """
    genre = GenresSerializer(many=True)
    category = CategoriesSerializer()
    rating = serializers.IntegerField(
        source='reviews__score__avg', read_only=True
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'genre', 'category')
        extra_kwargs = {
            'description': {'required': False}
        }


class TitlesPostSerializer(serializers.ModelSerializer):
    """Сериализатор для создания или обновления обьектов Titles.

    Обрабатывает:
    POST-запросы для создания новых объектов Title.
    PATCH-запросы для обновления существующих
    объектов Title по id.

    Заданы уникальные поля для избежания создания одинаковых
    произведений с помощью UniqueTogetherValidator.
    """
    genre = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Genre.objects.all()
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'genre', 'category')
        extra_kwargs = {
            'description': {'required': False}
        }

        validators = [
            UniqueTogetherValidator(
                queryset=Title.objects.all(),
                fields=['name', 'year'],
                message='Такое произведение уже существует.'
            )
        ]

    def validate_year(self, value):
        """Проверяем что год выпуска не может быть больше текущего
        или отрицательным.
        """
        if value > date.today().year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего года.')
        elif value < 0:
            raise serializers.ValidationError(
                'Год выпуска не может быть отрицательным.')
        return value


class GenreTitleSerializer(serializers.ModelSerializer):
    """Сериализатор модели Genres."""
    class Meta:
        fields = '__all__'
        model = GenreTitle


class ReviewsSerializer(serializers.ModelSerializer):
    """Сериализатор модели Reviews."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        model = Review


class CommentsSerializer(serializers.ModelSerializer):
    """Сериализатор модели Comments."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment
