from django.conf import settings

def site_info(request):
    """Добавляет общую информацию о сайте в контекст всех шаблонов"""
    return {
        'site_name': 'ЭкоБезопасность',
        'site_description': 'АНО "ЭкоБезопасность" - защита окружающей среды',
        'phone': '+7 (999) 123-45-67',
        'email': 'info@ecobezopasnost.ru',
        'address': 'г. Москва, ул. Экологическая, д. 1',
    }