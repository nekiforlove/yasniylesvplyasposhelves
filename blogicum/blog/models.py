from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseModel(models.Model):
    is_published = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True


class Location(BaseModel):
    name = models.CharField(
        max_length=256,
        null=False,
        verbose_name='Название места'
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Category(BaseModel):
    title = models.CharField(
        max_length=256,
        null=False,
        verbose_name='Заголовок'
    )
    description = models.TextField(
        null=False,
        verbose_name='Описание'
    )
    slug = models.SlugField(
        unique=True,
        null=False,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; разрешены символы '
            'латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return f'{self.title}|{self.slug}'


class Post(BaseModel):
    title = models.CharField(
        max_length=256,
        null=False,
        verbose_name='Заголовок'
    )
    text = models.TextField(
        null=False,
        verbose_name='Текст'
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    pub_date = models.DateTimeField(
        null=False,
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='posts',
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name='Категория'
    )

    @classmethod
    def published(cls):
        return cls.objects.select_related(
            'category',
            'location',
            'author'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

    @property
    def comment_count(self):
        return self.comments.count()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return f'{self.title}|{self.author}'


class Comment(BaseModel):
    text = models.TextField(
        null=False,
        verbose_name='Текст комментария'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=False,
        related_name='comments',
        verbose_name='Публикация'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='comments',
        verbose_name='Автор комментария'
    )

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий от {self.author} к посту «{self.post.title}»'
