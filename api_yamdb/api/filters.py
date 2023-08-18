from django_filters import rest_framework as filters

from reviews.models import Title


class TitlesFilter(filters.FilterSet):
    """Добавляем возможность фильтрации по полю "slug"
    для полей "category" и "genre".

    Создаем класс TitlesFilter, который наследуется от filters.FilterSet.
    Внутри этого класса мы определяем два поля фильтрации:
    category_slug и genre_slug.
    Оператор сравнения lookup_expr='icontains' будет искать
    небходимые данные среди записей.
    """
    category = filters.CharFilter(field_name='category__slug',
                                  lookup_expr='icontains')
    genre = filters.CharFilter(field_name='genre__slug',
                               lookup_expr='icontains')
    name = filters.CharFilter(field_name='name',
                              lookup_expr='icontains')
    year = filters.CharFilter(field_name='year',
                              lookup_expr='icontains')

    class Meta:
        model = Title
        fields = ['category', 'genre', 'name', 'year']
