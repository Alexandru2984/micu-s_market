from django.shortcuts import render

# Create your views here.

def reviews_for_user_view(request):
	context = {}
	return render(request, 'reviews/for_user.html', context)

def create_review(request):
	context = {}
	return render(request, 'reviews/create.html', context)
