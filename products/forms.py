from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "class": "border rounded p-2"}),
            "comment": forms.Textarea(attrs={"class": "border rounded p-2 w-full"}),
        }
