from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from favorites.models import SavedSearch

from .forms import SavedSearchForm

# Create your views here.

def search_view(request):
	context = {}
	return render(request, 'search/search.html', context)

def advanced_search_view(request):
	context = {}
	return render(request, 'search/advanced.html', context)


@login_required
def saved_searches_view(request):
	if request.method == "POST":
		form = SavedSearchForm(request.POST)
		if form.is_valid():
			saved_search = form.save(commit=False)
			saved_search.user = request.user
			saved_search.save()
			messages.success(request, "Căutarea a fost salvată.")
			return redirect("search:saved_searches")
	else:
		form = SavedSearchForm()

	context = {
		"form": form,
		"saved_searches": SavedSearch.objects.filter(user=request.user).select_related("category"),
	}
	return render(request, 'search/saved.html', context)


@login_required
def run_saved_search_view(request, pk):
	saved_search = get_object_or_404(SavedSearch, pk=pk, user=request.user, is_active=True)
	params = saved_search.get_search_params()
	if "q" in params:
		params["search"] = params.pop("q")
	if saved_search.category:
		params["category"] = saved_search.category.slug
	query = urlencode({key: value for key, value in params.items() if value not in (None, "")})
	url = reverse("listings:list")
	return redirect(f"{url}?{query}" if query else url)


@login_required
@require_POST
def toggle_saved_search_view(request, pk):
	saved_search = get_object_or_404(SavedSearch, pk=pk, user=request.user)
	saved_search.is_active = not saved_search.is_active
	saved_search.save(update_fields=["is_active", "updated_at"])
	return redirect("search:saved_searches")


@login_required
@require_POST
def delete_saved_search_view(request, pk):
	saved_search = get_object_or_404(SavedSearch, pk=pk, user=request.user)
	saved_search.delete()
	messages.success(request, "Căutarea salvată a fost ștearsă.")
	return redirect("search:saved_searches")
