from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category
from django.contrib.admin.views.decorators import staff_member_required
from .models import CarouselItem
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Review
from .forms import ReviewForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from  cart.models import Order, OrderItem
from django.db.models import Sum, Count
import datetime




@staff_member_required
def admin_dashboard(request):
    # Seul le staff peut accéder
    return render(request, 'admin/dashboard.html')

def product_list(request, category=None):
    carousel_items = CarouselItem.objects.all()
    categories = Category.objects.all()
    products = Product.objects.all()
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category:
        category = get_object_or_404(Category, slug=category)
        products = products.filter(category=category)
    context = {
        'carousel_items': carousel_items,
        'categories': categories,
        'products': products,
        'category': category,
        'query': query,
    }
    
    
    return render(request, 'products/list.html', context )
    






def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    
    # Récupérer les images supplémentaires du produit
    additional_images = product.images.all()
    
    # Récupérer les produits similaires (même catégorie, sauf le produit actuel)
    similar_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    # Récupérer les avis, triés par date de création (du plus récent au plus ancien)
    reviews = product.reviews.all().order_by('-created')
    
    # Fournir le formulaire d'avis pour affichage
    form = ReviewForm()
    
    # Vérifier si l'utilisateur a déjà un avis (seulement si authentifié)
    user_has_review = False
    if request.user.is_authenticated:
        user_has_review = Review.objects.filter(product=product, user=request.user).exists()
    
    context = {
        "product": product,
        "additional_images": additional_images,
        "similar_products": similar_products,
        "reviews": reviews,
        "form": form,
        "category": product.category,  # Inclure la catégorie pour la navigation
        'user_has_review': user_has_review,
    }
    
    return render(request, "products/detail.html", context)


def product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ) if query else Product.objects.all()

    results = []
    for product in products:
        results.append({
            "id": product.id,
            "name": product.name,
            "description": product.description[:50] + "...",
            "price": f"{product.get_price_fcfa()} FCFA",
            "image": product.main_image.url if product.main_image else "",
        })

    return JsonResponse({"results": results})








def check_user_purchase(user, product):
    """
    Vérifie si un utilisateur a déjà acheté un produit donné.
    """
    if not user.is_authenticated:
        return False
    
    return Order.objects.filter(
        user=user,
        items__product=product,
        paid=True,
        payment_status="succeeded"
    ).exists()


@login_required
def add_review(request, id):
    """Ajouter ou modifier un avis (seulement pour utilisateurs connectés)"""
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Créer ou mettre à jour l'avis
            review, created = Review.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment']
                }
            )
            
            if created:
                messages.success(request, "Votre avis a été enregistré avec succès!")
            else:
                messages.success(request, "Votre avis a été mis à jour avec succès!")
            
            return redirect('product_detail', id=product.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        # Pré-remplir le formulaire si l'utilisateur a déjà un avis
        try:
            existing_review = Review.objects.get(product=product, user=request.user)
            form = ReviewForm(instance=existing_review)
        except Review.DoesNotExist:
            form = ReviewForm()
    
    # Afficher la page détaillée du produit avec le formulaire
    reviews = product.reviews.all().order_by('-created')
    
    context = {
        'product': product,
        'reviews': reviews,
        'review_form': form,
        'user_has_review': Review.objects.filter(product=product, user=request.user).exists(),
    }
    
    return render(request, 'products/product_detail.html', context)

