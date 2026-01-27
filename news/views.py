from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import News

def news_list(request):
    """Список всех новостей"""
    news_list = News.objects.filter(is_published=True).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(news_list, 9)  # По 9 новостей на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'news/news_list.html', {
        'page_obj': page_obj,
    })

def news_detail(request, pk):
    """Детальная страница новости"""
    news = get_object_or_404(News, pk=pk, is_published=True)
    
    # Получаем предыдущую и следующую новости
    previous_news = News.objects.filter(
        is_published=True,
        created_at__lt=news.created_at
    ).order_by('-created_at').first()
    
    next_news = News.objects.filter(
        is_published=True,
        created_at__gt=news.created_at
    ).order_by('created_at').first()
    
    return render(request, 'news/news_detail.html', {
        'news': news,
        'previous_news': previous_news,
        'next_news': next_news,
    })

def news_homepage(request):
    """Последние новости для главной страницы"""
    latest_news = News.objects.filter(is_published=True).order_by('-created_at')[:6]
    return render(request, 'news/includes/news_homepage.html', {'latest_news': latest_news})