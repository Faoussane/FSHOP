"""
URL configuration for faouxlab_ecom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path('cart/', include('cart.urls', namespace='cart')),

    # Exempter CSRF au niveau URL et placer avant l'include racine
    path("chatbot/", csrf_exempt(views.chatbot_response), name="chatbot"),
    path("chatbot/history/", views.get_chat_history, name="chatbot_history"),

    path('', include('products.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    
    path('payments/', include('payments.urls', namespace='payments')),
    
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)