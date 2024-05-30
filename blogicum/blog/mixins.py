from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse

from .forms import User
from .models import Post, Comment


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        if self.model == User:
            return self.get_object() == self.request.user
        return self.get_object().author == self.request.user


class CustomSuccessUrlMixin:
    success_url_name = ''

    def get_success_url(self):
        post_url = 'blog:post_detail'
        if self.success_url_name == 'post_id':
            if self.model == Post:
                post_kwargs = {'post_id': self.object.id}
            else:
                post_kwargs = {'post_id': self.object.post.id}
        else:
            post_url = 'blog:profile'
            post_kwargs = {'username': self.request.user.username}
        return reverse(post_url, kwargs=post_kwargs)


class CommentMixin(CustomSuccessUrlMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    fields = '__all__'
