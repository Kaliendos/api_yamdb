from api.filters import TitlesFilter

from api.permissions import (IsAdmin, IsAdminOrReadOnly,
                             IsAuthorModeratorAdminOrReadOnly)
from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, ReviewSerializer,
                             SignUpSerializer, TitlesSerializer,
                             TokenSerializer, UserMeSerializer, UserSerializer)
from api.utils import send_mail_function
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAdminUser, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title, User, Comment


@api_view(["POST"])
def register_user(request):
    """Регистрация нового пользователя """
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user = get_object_or_404(
        User,
        username=serializer.validated_data["username"]
    )
    confirmation_code = default_token_generator.make_token(user)
    send_mail_function(user, confirmation_code)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def get_token_for_users(request):
    """Получить токен"""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User,
        username=serializer.validated_data["username"]
    )
    if default_token_generator.check_token(
            user,
            serializer.validated_data["confirmation_code"]):
        token = AccessToken.for_user(user)
        return Response({"token": token},
                        status=status.HTTP_200_OK)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    """Логика работы с пользователями"""
    queryset = User.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ("username",)
    lookup_field = "username"
    permission_classes = (IsAdmin | IsAdminUser,)

    def get_serializer_class(self):
        """
        Возвращает сериализатор в зависимости
        от роли пользователя
        """
        if self.request.user.role == "user":
            return UserMeSerializer
        return UserSerializer

    @action(methods=["GET", "PATCH"],
            url_path="me", detail=False,
            permission_classes=(IsAuthenticated,),
            )
    def users_profile(self, request):
        """Метод обрабатывает запрос users/me"""
        serializer = self.get_serializer(self.request.user)
        if request.method == "PATCH":
            serializer = self.get_serializer(
                self.request.user,
                data=request.data,
                partial=True)
            serializer.is_valid()
            serializer.save()
        return Response(serializer.data)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"
    permission_classes = (IsAdminOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH')


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"
    permission_classes = (IsAdminOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH')


class TitlesViewSet(ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitlesSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    permission_classes = (IsAdminOrReadOnly,)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthorModeratorAdminOrReadOnly,
        IsAuthenticatedOrReadOnly
    ]

    def get_queryset(self):
        return Review.objects.filter(title__id=self.kwargs['title_id'])

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthorModeratorAdminOrReadOnly,
        IsAuthenticatedOrReadOnly
    ]

    def get_queryset(self):
        return Comment.objects.filter(review__id=self.kwargs['review_id'])

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review, id=self.kwargs['review_id'],
            title__id=self.kwargs['title_id']
        )
        serializer.save(author=self.request.user, review=review)
