from django.contrib.auth.mixins import (
    UserPassesTestMixin, LoginRequiredMixin
)
from django.db.models import Count
from django.http import Http404
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .forms import CommentForm, CustomUserCreationForm
from .models import Post, Category, Comment

User = get_user_model()


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


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


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.published.all()
        queryset = queryset.annotate(comment_count=Count('comments'))
        return queryset


class ProfileView(ListView):
    template_name = 'blog/profile.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(author=get_object_or_404(
            User,
            username=self.kwargs.get('username')),
        ).order_by('-pub_date', 'title')
        queryset = queryset.annotate(comment_count=Count('comments'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )
        return context


class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = [
        'username',
        'first_name',
        'last_name',
        'email',
        'last_login',
        'date_joined'
    ]
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )

    def test_func(self):
        obj = self.get_object()
        return obj == self.request.user


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.all()

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if (
            not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()
        ) and request.user != post.author:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostCreateView(
    CustomSuccessUrlMixin, LoginRequiredMixin, CreateView
):
    model = Post
    template_name = 'blog/create.html'
    fields = [
        'title',
        'text',
        'pub_date',
        'image',
        'location',
        'category'
    ]
    success_url_name = 'username'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(
    CustomSuccessUrlMixin, OnlyAuthorMixin, UpdateView
):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    fields = [
        'title',
        'text',
        'pub_date',
        'image',
        'location',
        'category'
    ]
    success_url_name = 'post_id'

    def handle_no_permission(self):
        post_id = self.kwargs.get('post_id')
        return redirect('blog:post_detail', post_id=post_id)


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CustomUserCreationForm(instance=self.object)
        return context


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category.objects.filter(is_published=True),
            slug=self.kwargs.get('category_slug')
        )
        queryset = Post.published.filter(category=self.category)
        queryset = queryset.annotate(comment_count=Count('comments'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class AddCommentView(
    CustomSuccessUrlMixin, LoginRequiredMixin, CreateView
):
    model = Comment
    form_class = CommentForm
    success_url_name = 'post_id'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)


class CommentUpdateView(CommentMixin, OnlyAuthorMixin, UpdateView):
    pass


class CommentDeleteView(CommentMixin, OnlyAuthorMixin, DeleteView):
    pass
