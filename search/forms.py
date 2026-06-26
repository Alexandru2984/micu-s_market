from django import forms

from categories.models import Category
from favorites.models import SavedSearch


class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = [
            "name",
            "search_query",
            "category",
            "min_price",
            "max_price",
            "city",
            "county",
            "email_notifications",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Laptopuri în Cluj"}),
            "search_query": forms.TextInput(attrs={"class": "form-control", "placeholder": "Termen căutare"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "min_price": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "max_price": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Oraș"}),
            "county": forms.TextInput(attrs={"class": "form-control", "placeholder": "Județ"}),
            "email_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by("name")
        self.fields["category"].required = False

    def clean(self):
        cleaned = super().clean()
        min_price = cleaned.get("min_price")
        max_price = cleaned.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise forms.ValidationError("Prețul minim nu poate fi mai mare decât prețul maxim.")

        has_filter = any(
            cleaned.get(field)
            for field in ("search_query", "category", "min_price", "max_price", "city", "county")
        )
        if not has_filter:
            raise forms.ValidationError("Adaugă cel puțin un filtru pentru căutarea salvată.")
        return cleaned
