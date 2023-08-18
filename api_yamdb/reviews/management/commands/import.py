import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from reviews.models import (Category, Comment, Genre, GenreTitle, Review,
                            Title, User)

MODELS = {
    User: 'users.csv',
    Category: 'category.csv',
    Genre: 'genre.csv',
    Title: 'titles.csv',
    GenreTitle: 'genre_title.csv',
    Review: 'review.csv',
    Comment: 'comments.csv',
}

FOREIGN_KEY_FIELDS = ('category', 'genre', 'title', 'author')

BASE_DIR = settings.BASE_DIR
STATIC_DIR = os.path.join(BASE_DIR, 'static', 'data')


def check_field(csv_data, model):
    """Проверка поля/столбца таблицы.

    Так как Python автоматически добавляет '_id' к названию поля
    которому задан ForeignKey, выполняем проверку
    чтобы избежать дублирования '_id_id'.
    """
    checked_fields = []
    for row in csv_data:
        for field in FOREIGN_KEY_FIELDS:
            if field in row:
                field_name = f'{field}_id'
                if not field_name.endswith('_id'):
                    field_name += '_id'
                try:
                    row[field_name] = row.pop(field)
                except KeyError:
                    pass
        checked_fields.append(model(**row))
    model.objects.bulk_create(checked_fields)


def get_file_name(file_path):
    """Получаем название файла.

    Функция os.path.basename() возвращает
    базовое имя пути - '/.../.../filename.csv'
    """
    return os.path.basename(file_path)


def open_csv(csv_file_path, model):
    """Открываем csv фаилы и проверяем их коректность."""
    csv_data = []
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            csv_data.append(row)
    records = check_field(csv_data, model)
    model.objects.bulk_create(records)


class Command(BaseCommand):
    help = 'Импорт данных из CSV в DB'

    def handle(self, *args, **kwargs):
        """В директории с расположением файла manage.py
        можно выполнить команду python manage.py import
        для импорта данных из файлов csv в таблицы.
        """
        for model, csv_file in MODELS.items():
            csv_file_path = os.path.join(STATIC_DIR, csv_file)
            file_name = get_file_name(csv_file_path)
            try:
                open_csv(csv_file_path, model)
                self.stdout.write(self.style.SUCCESS(
                    f'Данные из {file_name} загружены в базу данных.'))
            except FileNotFoundError:
                self.stderr.write(self.style.ERROR(
                    f'Фаил {csv_file} не найден.'))
