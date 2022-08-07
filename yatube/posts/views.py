from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .models import Comment, Follow, Group, Post
from .forms import CommentForm, PostForm
from .utils import get_page_count

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    context = {
        'page_obj': get_page_count(Post.objects.select_related(
            'author', 'group'), request)
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
        'page_obj': get_page_count(group.posts.select_related(
            'author', 'group'), request)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists()
                 )
    context = {
        'author': author,
        'page_obj': get_page_count(author.posts.select_related(
            'author', 'group'), request),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    user_post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = Comment.objects.select_related('post').filter(post=user_post)
    context = {
        'user_post': user_post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    form.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    context = {
        'page_obj': get_page_count(Post.objects.filter(
            author__following__user=request.user), request)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', request.user.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', request.user.username)
