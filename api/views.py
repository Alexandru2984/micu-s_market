from django.shortcuts import render

# Create your views here.

def api_listing_list_view(request):
	context = {}
	return render(request, 'api/listings_list.html', context)

def api_listing_detail_view(request):
	context = {}
	return render(request, 'api/listings_detail.html', context)

def api_create_listing_view(request):
	context = {}
	return render(request, 'api/create_listing.html', context)
