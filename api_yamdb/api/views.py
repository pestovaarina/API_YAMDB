import uuid

from api.filters import TitlesFilter
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api_yamdb.settings import ADMIN_EMAIL
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsOwnerAdminModeratorOrReadOnly)
from .serializers import (CategoriesSerializer, CommentsSerializer,
                          GenresSerializer, GenreTitleSerializer,
                          ReviewsSerializer, SignupSerializer,
                          TitlesPostSerializer, TitlesSerializer,
                          TokenSerializer, UserSerializer)
from reviews.models import (Category, Comment, Genre, GenreTitle, Review,
                            Title, User)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('username', )
    lookup_field = 'username'
    http_method_names = ('get', 'post', 'patch', 'delete')
    pagination_class = PageNumberPagination

    @action(
        detail=False,
        methods=['GET', 'PATCH'],
        url_path='me',
        permission_classes=(IsAuthenticated, ))
    def change_user_info(self, request):
        """
        Позволяет пользователю получить подробную информацию о себе
        и редактировать её.
        """
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    Пользователь отправляет свои 'username' и 'email' на 'auth/signup/ и
    получает код подтверждения на email.
    """

    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    email = serializer.validated_data['email']
    confirmation_code = uuid.uuid4().hex
    try:
        if User.objects.filter(email=email, username=username).exists():
            user = User.objects.get(username=username, email=email)
            user.confirmation_code = confirmation_code
            user.save()
        else:
            user = User.objects.create(
                **serializer.validated_data,
                confirmation_code=confirmation_code
            )
    except IntegrityError:
        raise serializers.ValidationError(
            'Данные имя пользователя или Email уже зарегистрированы.')
    send_mail(
        subject='Код подтверждения',
        message=f'{confirmation_code} - Код для авторизации на сайте',
        from_email=ADMIN_EMAIL,
        recipient_list=[user.email],
        fail_silently=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def token(request):
    """
    Пользователь отправляет свои 'username' и 'confirmation_code'
    на 'auth/token/ и получает токен.
    """

    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = request.data['username']
    confirmation_code = serializer.data['confirmation_code']
    user = get_object_or_404(User, username=username)
    if user.confirmation_code != confirmation_code:
        return Response(
            'Код подтверждения неверный', status=status.HTTP_400_BAD_REQUEST
        )
    refresh = RefreshToken.for_user(user)
    token_data = {'token': str(refresh.access_token)}
    return Response(token_data, status=status.HTTP_200_OK)


class CreateListDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """Вьюсет, который будет уметь:

    Создавать объект (для обработки запросов POST)
    Возвращать список объектов (для обработки запросов GET)
    Удалять объект (для обработки запросов DELETE)
    """
    pass


class TitlesViewSet(viewsets.ModelViewSet):
    """Вьюсет для произведений."""
    queryset = Title.objects.all().annotate(Avg('reviews__score')).\
        select_related('category').prefetch_related('genre')
    serializer_class = TitlesSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        """Определяем какой из доступных сериализаторов должен
        обрабатывать данные(GET или POST,PATCH).

        TitlesSerializer обрабатывет:
        GET-запросы для получения списка объектов Title.
        GET-запросы для получения конкретного объекта Title по его id.

        TitlesPostSerializer обрабатывает:
        POST-запросы для создания новых объектов Title.
        PATCH-запросы для обновления существующих
        объектов Title по id.
        """
        if self.action in ('list', 'retrieve'):
            return TitlesSerializer
        return TitlesPostSerializer


class CategoriesViewSet(CreateListDestroyViewSet):
    """Унаследовались от кастомного вью сета
    чтобы задать определенный функционал.
    """
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'slug',)
    lookup_field = 'slug'


class GenresViewSet(CreateListDestroyViewSet):
    """Унаследовались от кастомного вью сета
    чтобы задать определенный функционал.
    """
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'slug',)
    lookup_field = 'slug'


class GenresTitles(viewsets.ModelViewSet):
    """Вьюсет для модели посредника."""
    queryset = GenreTitle.objects.all()
    serializer_class = GenreTitleSerializer


class ReviewsViewSet(viewsets.ModelViewSet):
    """Вьюсет для ревью."""
    queryset = Review.objects.all()
    serializer_class = ReviewsSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsOwnerAdminModeratorOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all()

    def create(self, request, *args, **kwargs):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        user = request.user

        if Review.objects.filter(author=user, title=title).exists():
            return Response(
                {'detail': 'Отзыв уже оставлен!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=user, title=title)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)


class CommentsViewSet(viewsets.ModelViewSet):
    """Вьюсет для коментариев."""
    queryset = Comment.objects.all()
    serializer_class = CommentsSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsOwnerAdminModeratorOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs['review_id'],
            title__id=self.kwargs['title_id']
        )
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs['review_id'],
            title__id=self.kwargs['title_id']
        )
        serializer.save(author=self.request.user, review=review)

    def create(self, request, *args, **kwargs):
        review = get_object_or_404(Review, id=self.kwargs['review_id'],
                                   title__id=self.kwargs['title_id'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, review=review)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
