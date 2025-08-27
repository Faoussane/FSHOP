from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from products.models import Product
import stripe
from django.conf import settings
from .cart import Cart
from .forms import CartAddProductForm
from .orders import create_order, send_order_confirmation
from django.contrib import messages 
from django.urls import reverse
from django.http import JsonResponse



def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})






@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'])

        # ✅ Réponse JSON pour appels AJAX (aucune redirection)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "product_id": product.id,
                "quantity_added": cd["quantity"],
                "cart_count": len(cart),
                "cart_total": float(cart.get_total_price()),  # ⚠️ float sinon erreur JSON
                "message": "Produit ajouté au panier"
            })

    # ⏪ Fallback: redirection si pas AJAX
    return redirect("product_list")  # vérifie bien que le namespace correspond


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:detail')


# Traiter la commande

stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout(request):
    cart = Cart(request)

    if request.method == 'POST':
        # données invité si non connecté
        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')

        if 'confirm_order' in request.POST:
            # Commande sans paiement en ligne
            if request.user.is_authenticated:
                order = create_order(request, cart, address=address)
                recipient = request.user.email
            else:
                # validation minimale
                if not (name and email and address):
                    messages.error(request, "Veuillez renseigner nom, email et adresse.")
                    return render(request, 'cart/checkout.html', {'cart': cart})
                order = create_order(request, cart, name=name, email=email, address=address)
                recipient = email

            cart.clear()
            send_order_confirmation(recipient, order)
            messages.success(request, "Commande confirmée avec succès.")
            return render(request, 'cart/checkout_done.html', {'order': order})

        elif 'pay_online' in request.POST:
            # D’abord créer la commande, puis rediriger vers Stripe
            if request.user.is_authenticated:
                order = create_order(request, cart, address=address)
                customer_email = request.user.email
            else:
                if not (name and email and address):
                    messages.error(request, "Veuillez renseigner nom, email et adresse.")
                    return render(request, 'cart/checkout.html', {'cart': cart})
                order = create_order(request, cart, name=name, email=email, address=address)
                customer_email = email

            # XOF = zero-decimal → pas de *100
            amount = int(order.total)

            session = stripe.checkout.Session.create(
                payment_method_types=['card', 'link'],
                line_items=[{
                    'price_data': {
                        'currency': 'xof',
                        'product_data': {'name': f"Commande #{order.id}"},
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=customer_email,
                success_url=request.build_absolute_uri(
                    reverse('payments:success')
                ) + f'?order_id={order.id}',
                cancel_url=request.build_absolute_uri(
                    reverse('payments:cancel')
                ) + f'?order_id={order.id}',
            )

            order.payment_id = session.id
            order.save()

            # ⚠️ ne vide PAS le panier ici si tu comptes t’appuyer sur le webhook pour confirmer le paiement.
            # Si c’est juste pour la démo, tu peux vider ici — mais mieux vaut le faire sur success/webhook.
            return redirect(session.url, code=303)

    return render(request, 'cart/checkout.html', {'cart': cart})




@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        cd = form.cleaned_data
        # override=True remplace la quantité au lieu d'ajouter
        cart.add(product=product,
                 quantity=cd['quantity'],
                 override_quantity=cd.get('override', False))
    
    return redirect('cart:detail')
