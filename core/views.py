from django.shortcuts import render
from news.models import News
from docs.models import Document

def home(request):
    """Главная страница сайта"""
    # Получаем последние 6 опубликованных новостей
    latest_news = News.objects.filter(is_published=True).order_by('-created_at')[:6]
    
    # Получаем последние 5 документов
    latest_documents = Document.objects.filter(is_published=True).order_by('-uploaded_at')[:5]
    
    context = {
        'latest_news': latest_news,
        'latest_documents': latest_documents,
    }
    return render(request, 'core/home.html', context)