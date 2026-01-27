from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import FileResponse
from .models import Document, DocumentCategory

def document_list(request):
    """Список документов с поиском и фильтрацией"""
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '')
    
    documents = Document.objects.filter(is_published=True)
    
    # Фильтрация по категории
    if category_slug:
        documents = documents.filter(category__slug=category_slug)
    
    # Поиск
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Сортировка по алфавиту
    documents = documents.order_by('title')
    
    # Получаем все категории для фильтра
    categories = DocumentCategory.objects.all()
    
    # Получаем текущую категорию
    current_category = None
    if category_slug:
        current_category = DocumentCategory.objects.filter(slug=category_slug).first()
    
    return render(request, 'docs/document_list.html', {
        'documents': documents,
        'categories': categories,
        'current_category': current_category,
        'search_query': search_query,
    })

def document_download(request, pk):
    """Увеличивает счетчик скачиваний и отдает файл"""
    document = get_object_or_404(Document, pk=pk, is_published=True)
    document.download_count += 1
    document.save()
    
    response = FileResponse(document.file.open(), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
    return response