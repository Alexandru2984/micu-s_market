from django.shortcuts import render

# Create your views here.

def search_view(request):
	context = {}
	return render(request, 'search/search.html', context)

def advanced_search_view(request):
	context = {}
	return render(request, 'search/advanced.html', context)

def saved_searches_view(request):
	context = {}
	return render(request, 'search/saved.html', context)
