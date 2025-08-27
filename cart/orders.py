from django.core.mail import send_mail
from .models import Order, OrderItem
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives



def create_order(request, cart, name=None, email=None, address=None):
    """
    Crée une commande pour un utilisateur connecté OU invité.
    - name/email/address sont utilisés pour les invités.
    """
    if request.user.is_authenticated:
        user = request.user
        guest_name = ''
        guest_email = request.user.email or ''
    else:
        user = None
        guest_name = name or ''
        guest_email = email or ''

    order = Order.objects.create(
        user=user,
        guest_name=guest_name,
        guest_email=guest_email,
        shipping_address=address or '',
        total=cart.get_total_price()
    )

    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            price=item['price'],
            quantity=item['quantity']
        )

    # tu peux déclencher l’email ici si tu veux, ou dans la vue selon le bouton
    return order



def send_order_confirmation(email, order):
    if not email:
        return
    subject = f"Confirmation de commande #{order.id} - FaouxLab"
    
    # Génération du contenu HTML + fallback texte
    html_content = render_to_string("emails/order_confirmation.html", {"order": order})
    text_content = f"Merci pour votre commande #{order.id}. Total : {order.total} FCFA."
    
    msg = EmailMultiAlternatives(subject, text_content, None, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
