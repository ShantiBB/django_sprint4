from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .forms import CommentForm, CustomUserCreationForm
from .models import Post, Category, Comment
from .mixins import (
    OnlyAuthorMixin, CommentMixin, CustomSuccessUrlMixin
)

User = get_user_model()


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.custom_obj.is_published().with_comment_count()


class ProfileView(ListView):
    template_name = 'blog/profile.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        author = get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )
        return (
            Post.custom_obj.filter(author=author)
            .order_by('-pub_date', 'title').with_comment_count()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )
        return context


class ProfileUpdateView(OnlyAuthorMixin, UpdateView):
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


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.custom_obj.get_post(self.request.user)

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
        return (
            Post.custom_obj.is_published().with_comment_count().
            filter(category=self.category)
        )

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
