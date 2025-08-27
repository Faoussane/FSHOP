from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Product, Category, ProductImage
from .models import CarouselItem
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import redirect

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    can_delete = True
    verbose_name = "Image secondaire"
    verbose_name_plural = "Images secondaires"

# Désinscription du modèle Group (optionnel)
admin.site.unregister(Group)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]
    # Seul l'admin peut modifier
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Mêmes restrictions que pour Product
    def has_module_permission(self, request):
        return request.user.is_superuser
    


admin.site.register(CarouselItem)




# Ajouter un lien dans la page d'accueil de l'admin
admin.site.site_header = "Gestion E-Commerce"
admin.site.index_title = "Administration"
admin.site.site_title = "E-Commerce Admin"

def admin_dashboard_link():
    return format_html('<a href="/admin/dashboard/" class="button">⚡ Dashboard</a>')

admin.site.index_template = "admin/index.html"
