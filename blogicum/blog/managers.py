from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone


# Переделал менеджер поста, чтобы вынести логику редиректа в
# деталях поста и логику подсчета комментариев
class PostQuerySet(models.QuerySet):

    def is_published(self):
        return self.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date', 'title')

    def get_post(self, user):
        if isinstance(user, AnonymousUser):
            return self.is_published()
        return self.filter(
            Q(
                is_published=True, category__is_published=True,
                pub_date__lte=timezone.now()
            ) | Q(author=user)
        )

    def with_comment_count(self):
        return self.annotate(comment_count=Count('comments'))


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def is_published(self):
        return self.get_queryset().is_published()

    def get_post(self, user):
        return self.get_queryset().get_post(user)

    def with_comment_count(self):
        return self.get_queryset().with_comment_count()
