from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', lambda request: redirect('/accounts/login/')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='standalone_login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('core.urls')),
]
