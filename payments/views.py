
import stripe
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from cart.cart import Cart   # ta classe de panier (session)
from cart.models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY

def _to_stripe_amount(amount_decimal: Decimal) -> int:
    # Stripe attend des centimes (int)
    # On arrondit proprement (2 décimales, EUR)
    cents = (amount_decimal * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(cents)

@require_POST
def create_checkout_session(request):
    # 1) Vérifier qu'on a un panier
    cart = Cart(request)
    if len(cart) == 0:
        return JsonResponse({'error': 'Votre panier est vide.'}, status=400)

    # 2) Créer l’Order en "draft" (paid=False)
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        total=cart.get_total_price(),
        paid=False
    )
    # 3) Créer les OrderItems à partir du panier
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            price=item['price'],
            quantity=item['quantity']
        )

    # 4) Construire les line_items pour Stripe
    line_items = []
    for item in order.items.all():
        line_items.append({
            'quantity': item.quantity,
            'price_data': {
                'currency': settings.STRIPE_CURRENCY,
                'unit_amount': _to_stripe_amount(item.price),
                'product_data': {
                    'name': item.product.name,
                    # Optionnel: 'images': [request.build_absolute_uri(item.product.main_image.url)] si image publique
                }
            },
        })

    # 5) Créer une session Stripe Checkout
    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        line_items=line_items,
        success_url=request.build_absolute_uri(
            f"/payments/success/?order_id={order.id}"
        ),
        cancel_url=request.build_absolute_uri(
            f"/payments/cancel/?order_id={order.id}"
        ),
        metadata={
            "order_id": str(order.id)
        }
    )

    # 6) Retourner l’URL de redirection Stripe
    return JsonResponse({'checkout_url': session.url})

def payment_success(request):
    order_id = request.GET.get('order_id')
    if order_id:
        # On n’active "paid=True" que via webhook (source de vérité)
        # Ici, on affiche un message sympa + état courant
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return render(request, "payments/success.html", {"order": None, "paid": False})

        return render(request, "payments/success.html", {"order": order, "paid": order.paid})
    return render(request, "payments/success.html", {"order": None, "paid": False})

def payment_cancel(request):
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order = None
    else:
        order = None
    return render(request, "payments/cancel.html", {"order": order})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=webhook_secret
            )
        except ValueError:
            return HttpResponse(status=400)  # payload invalide
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)  # signature invalide
    else:
        # En dev sans signature
        try:
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
        except Exception:
            return HttpResponse(status=400)

    # On traite l’événement de paiement réussi
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                order = None
            if order and not order.paid:
                order.paid = True
                order.save()
                # vider le panier côté session ? pas ici (pas de request),
                # on le vide déjà au succès côté UX si besoin.
    return HttpResponse(status=200)