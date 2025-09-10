from django.shortcuts import render

# Create your views here.

def category_list_view(request):
	context = {}
	return render(request, 'categories/list.html', context)

def category_detail_view(request):
	context = {}
	return render(request, 'categories/detail.html', context)

def subcategory_detail_view(request):
	context = {}
	return render(request, 'categories/subcategory_detail.html', context)
