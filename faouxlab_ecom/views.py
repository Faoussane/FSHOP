from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncHour
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from cart.models import Order, OrderItem
from django.utils.timezone import now, timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from mistralai import Mistral
import json
import os, requests
from django.conf import settings
import logging

@staff_member_required
def admin_dashboard(request):
    period = request.GET.get("period", "today")
    today = now().date()

    if period == "today":
        orders = Order.objects.filter(created__date=today)
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(hour=TruncHour("order__created"))
            .values("hour")
            .annotate(quantity=Sum("quantity"))
            .order_by("hour")
        )
        sales_data = [
            {"date": s["hour"].strftime("%H:%M"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
    elif period == "week":
        start_week = today - timedelta(days=today.weekday())
        orders = Order.objects.filter(created__date__gte=start_week)
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(date=TruncDate("order__created"))
            .values("date")
            .annotate(quantity=Sum("quantity"))
            .order_by("date")
        )
        sales_data = [
            {"date": s["date"].strftime("%d/%m"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
    elif period == "month":
        start_month = today.replace(day=1)
        orders = Order.objects.filter(created__date__gte=start_month)
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(date=TruncDate("order__created"))
            .values("date")
            .annotate(quantity=Sum("quantity"))
            .order_by("date")
        )
        sales_data = [
            {"date": s["date"].strftime("%d/%m"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
    else:  # all
        orders = Order.objects.all()
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(date=TruncDate("order__created"))
            .values("date")
            .annotate(quantity=Sum("quantity"))
            .order_by("date")
        )
        sales_data = [
            {"date": s["date"].strftime("%Y-%m"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]

    print(f"[admin_dashboard] Période: {period}, Commandes: {orders.count()}")
    print(f"[admin_dashboard] Sales data: {sales_data}")

    total_sales = orders.aggregate(total=Sum("total"))["total"] or 0
    total_orders = orders.count()
    total_customers = (
        orders.values("user").distinct().count() +
        orders.filter(user__isnull=True).values("guest_email").distinct().count()
    )

    recent_orders = orders.order_by("-created")

    return render(request, "admin/dashboard.html", {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "recent_orders": recent_orders,
        "sales_data": sales_data,
        "selected_period": period,
    })

def dashboard_view(request):
    period = request.GET.get("period", "today")
    today = now().date()

    if period == "today":
        orders = Order.objects.filter(created__date=today)
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(hour=TruncHour("order__created"))
            .values("hour")
            .annotate(quantity=Sum("quantity"))
            .order_by("hour")
        )
        sales_data = [
            {"date": s["hour"].strftime("%H:%M"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
        print(f"[dashboard_view] Période: {period}, Commandes: {orders.count()}")  # Log pour la période et le nombre de commandes
        print(f"[dashboard_view] Sales data: {sales_data}")  # Log pour les données
    elif period == "week":
        start_week = today - timedelta(days=today.weekday())
        orders = Order.objects.filter(created__date__gte=start_week)
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(date=TruncDate("order__created"))
            .values("date")
            .annotate(quantity=Sum("quantity"))
            .order_by("date")
        )
        sales_data = [
            {"date": s["date"].strftime("%d/%m"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
        print(f"[dashboard_view] Période: {period}, Commandes: {orders.count()}")
        print(f"[dashboard_view] Sales data: {sales_data}")
    elif period == "month":
        start_month = today.replace(day=1)
        orders = Order.objects.filter(created__date__gte=start_month)
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(date=TruncDate("order__created"))
            .values("date")
            .annotate(quantity=Sum("quantity"))
            .order_by("date")
        )
        sales_data = [
            {"date": s["date"].strftime("%d/%m"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
        print(f"[dashboard_view] Période: {period}, Commandes: {orders.count()}")
        print(f"[dashboard_view] Sales data: {sales_data}")
    else:  # all
        orders = Order.objects.all()
        sales_data = (
            OrderItem.objects.filter(order__in=orders)
            .annotate(date=TruncDate("order__created"))
            .values("date")
            .annotate(quantity=Sum("quantity"))
            .order_by("date")
        )
        sales_data = [
            {"date": s["date"].strftime("%Y-%m"), "quantity": float(s["quantity"])}
            for s in sales_data
        ]
        print(f"[dashboard_view] Période: {period}, Commandes: {orders.count()}")
        print(f"[dashboard_view] Sales data: {sales_data}")

    total_sales = orders.aggregate(total=Sum("total"))["total"] or 0
    total_orders = orders.count()
    total_customers = (
        orders.values("guest_email").distinct().count()
        + orders.exclude(user=None).values("user").distinct().count()
    )

    recent_orders = orders.order_by("-created")

    return render(request, "dashboard.html", {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "recent_orders": recent_orders,
        "sales_data": sales_data,
        "selected_period": period,
    })

logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def chatbot_response(request):
    logger.info("Requête reçue dans chatbot_response")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            logger.info(f"Message reçu : {user_message}")
            if not user_message:
                logger.warning("Message vide reçu")
                return JsonResponse({"error": "Message vide"}, status=400)

            # Créer ou récupérer la session de chat
            from products.models import ChatSession, ChatMessage
            chat_session, created = ChatSession.objects.get_or_create(user=request.user)
            
            # Sauvegarder le message de l'utilisateur
            ChatMessage.objects.create(
                session=chat_session,
                message_type='user',
                content=user_message
            )

            client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
            logger.info("Client Mistral initialisé")
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": "Tu es un assistant e-commerce concis. Donne des réponses COURTES et PRÉCISES en maximum 5 lignes. Sois direct et utile."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply = response.choices[0].message.content
            logger.info(f"Réponse de Mistral : {reply}")
            
            # Sauvegarder la réponse de l'assistant
            ChatMessage.objects.create(
                session=chat_session,
                message_type='assistant',
                content=reply
            )
            
            # Mettre à jour le timestamp de la session
            chat_session.save()
            
            return JsonResponse({"reply": reply})

        except Exception as e:
            logger.error(f"Erreur dans chatbot_response : {str(e)}")
            
            # Réponse de fallback si l'API est indisponible
            if "getaddrinfo failed" in str(e) or "connection" in str(e).lower():
                fallback_reply = "Désolé, je ne peux pas répondre pour le moment. Vérifiez votre connexion internet et réessayez."
            else:
                fallback_reply = f"Erreur technique : {str(e)}"
    
    return JsonResponse({"reply": fallback_reply})
    logger.warning("Méthode non autorisée")
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


@login_required
def get_chat_history(request):
    """Récupère l'historique des messages de l'utilisateur"""
    try:
        from products.models import ChatSession, ChatMessage
        chat_session = ChatSession.objects.filter(user=request.user).first()
        
        if chat_session:
            messages = chat_session.messages.all()
            history = []
            for msg in messages:
                history.append({
                    'type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime('%H:%M'),
                    'date': msg.timestamp.strftime('%d/%m/%Y')
                })
            return JsonResponse({'messages': history})
        return JsonResponse({'messages': []})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)