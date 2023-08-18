from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoriesViewSet, CommentsViewSet, GenresViewSet,
                    ReviewsViewSet, TitlesViewSet, UserViewSet, signup, token)

v1_router = DefaultRouter()

v1_router.register(r'categories', CategoriesViewSet, basename='categories')
v1_router.register(r'genres', GenresViewSet, basename='genres')
v1_router.register(r'titles', TitlesViewSet, basename='titles')
v1_router.register(r'reviews', ReviewsViewSet, basename='reviews')
v1_router.register(r'comments', CommentsViewSet, basename='comments')
v1_router.register('users', UserViewSet, basename='users')
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewsViewSet, basename='titles_reviews')
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentsViewSet, basename='titles_rev_comments')


urlpatterns = [
    path('v1/', include(v1_router.urls)),
    path('v1/auth/signup/', signup),
    path('v1/auth/token/', token),
]
