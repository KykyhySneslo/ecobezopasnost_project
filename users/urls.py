from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-verification-code/', views.resend_verification_code, name='resend_verification_code'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/delete-avatar/', views.delete_avatar, name='delete_avatar'),
]