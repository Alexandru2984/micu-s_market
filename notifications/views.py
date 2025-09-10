from django.shortcuts import render

# Create your views here.

def notifications_list_view(request):
	context = {}
	return render(request, 'notifications/list.html', context)

def mark_read_view(request):
	context = {}
	return render(request, 'notifications/mark_read.html', context)
