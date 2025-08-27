from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import CustomUserCreationForm
from .forms import CustomUserCreationForm, UserProfileForm
from django.contrib import messages
from cart.models import Order
from django.contrib.auth.decorators import login_required

from accounts.forms import UserProfileForm  # si tu as un formulaire profil
import logging


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mistralai import Mistral
import json
import os, requests
from django.conf import settings



logger = logging.getLogger(__name__)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')  # Évite de rendre le formulaire si déjà connecté
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.debug("User logged in: %s", user.username)
            return redirect('product_list')
        else:
            logger.debug("Invalid login attempt")
            return render(request, 'accounts/login.html', {
                'form': form,
                'error_message': 'Identifiants incorrects'
            })
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    logger.debug("Register view called")
    if request.user.is_authenticated:
        return redirect('product_list')  # Évite de rendre le formulaire si déjà connecté
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            logger.debug("Form valid, creating user: %s", user.username)
            login(request, user)
            return redirect('product_list')
        else:
            logger.debug("Invalid registration attempt: %s", form.errors)
            return render(request, 'accounts/register.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    logger.debug("User logged out")
    return redirect('product_list')

# accounts/views.py (extrait de profile_view)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            logger.debug("Profile updated for user: %s", request.user.username)
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('accounts:profile')
        else:
            logger.debug("Invalid profile update attempt: %s", form.errors)
    else:
        form = UserProfileForm(instance=request.user)

    # ✅ Récupérer les 5 dernières commandes de l'utilisateur
    transactions = Order.objects.filter(user=request.user).order_by('-created')[:5]

    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'form': form,
        'transactions': transactions
    })



