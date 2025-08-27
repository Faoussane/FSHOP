from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:id>/', views.product_detail, name='product_detail'),
    
    path('search/', views.product_search, name='product_search'),
    path('product/<int:id>/review/', views.add_review, name='add_review'),
    path('<slug:category>/', views.product_list, name='product_list_by_category'),
    
]