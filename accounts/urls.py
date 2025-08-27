from django.urls import path
from . import views

app_name = 'accounts'  # Définit le namespace

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
]
from django.conf import settings
from django.conf.urls.static import static

# urlpatterns = [
#     ...
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)