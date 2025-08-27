from django.urls import path
from . import views

app_name = 'cart'  # Namespace important

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('update/<int:product_id>/', views.cart_update, name='update'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('remove/<int:product_id>/', views.cart_remove, name='remove'),
    path('checkout/', views.checkout, name='checkout'),
]