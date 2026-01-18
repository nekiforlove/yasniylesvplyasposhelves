from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator


def paginate_queryset(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related(
        'author',
        'category',
        'location'
    ).order_by('-pub_date')
    page_obj = paginate_queryset(request, posts, per_page=10)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).select_related('author', 'location').order_by('-pub_date')
    page_obj = paginate_queryset(request, posts, per_page=10)
    context = {'category': category, 'page_obj': page_obj}
    return render(
        request,
        'blog/category.html',
        context
    )


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if (
        not post.is_published
        or post.pub_date > timezone.now()
        or not post.category.is_published
    ):
        if (
            not request.user.is_authenticated
            or post.author != request.user
        ):
            raise Http404("Пост не найден")

    comments = post.comments.select_related(
        'author'
    ).order_by('created_at')

    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    if request.user == profile_user:
        posts = Post.objects.filter(author=profile_user).select_related(
            'category',
            'location'
        ).order_by('-pub_date')
    else:
        posts = Post.objects.filter(
            author=profile_user,
            is_published=True,
            pub_date__lte=timezone.now()
        ).select_related('category', 'location').order_by('-pub_date')
    page_obj = paginate_queryset(request, posts, per_page=10)
    context = {'profile': profile_user, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    context = {'form': form}
    return render(request, 'blog/user.html', context)


@login_required
def post(request, pk=None):
    instance = get_object_or_404(Post, pk=pk) if pk else None

    if pk and instance.author != request.user:
        return redirect('blog:post_detail', pk=pk)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=instance
    )
    if request.method == 'POST' and form.is_valid():
        post_obj = form.save(commit=False)
        if not pk:
            post_obj.author = request.user
        post_obj.save()
        return redirect(
            'blog:profile',
            username=request.user.username
        )
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def post_delete(request, pk):
    instance = get_object_or_404(Post, pk=pk)
    if instance.author != request.user:
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        instance.delete()
        return redirect('blog:profile', username=request.user.username)
    form = PostForm(instance=instance)
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def comment(request, post_id, comment_id=None):
    post = get_object_or_404(Post, pk=post_id)

    if comment_id is not None:
        comment = get_object_or_404(Comment, pk=comment_id, post=post)
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=post_id)
    else:
        comment = None

    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.post = post
        new_comment.author = request.user
        new_comment.save()
        return redirect('blog:post_detail', pk=post_id)

    context = {'form': form, 'comment': comment}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)

    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=post_id)

    context = {'comment': comment}
    return render(request, 'blog/comment.html', context)
