from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Предоставляет права на осуществление запросов
    только аутентифицированному пользователю с ролью admin.
    """

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_admin)


class IsOwnerAdminModeratorOrReadOnly(permissions.BasePermission):
    """Доступно для создателя объекта, администратора, модератора,
    остальным только для чтения."""
    def has_permission(self, request, view):
        return any([request.method in permissions.SAFE_METHODS,
                    request.user.is_authenticated])

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or any([
                    request.user.is_admin,
                    request.user.is_moderator,
                    request.user == obj.author
                ]))


class IsAdminOrReadOnly(permissions.BasePermission):
    """Доступно только администратору, остальным только для чтения."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated
                    and request.user.is_admin))
