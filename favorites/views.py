from django.shortcuts import render

# Create your views here.

def favorites_list_view(request):
	context = {}
	return render(request, 'favorites/list.html', context)

def toggle_favorite_view(request):
	context = {}
	return render(request, 'favorites/toggle.html', context)
