from django.shortcuts import render

# Create your views here.

def inbox_view(request):
	context = {}
	return render(request, 'chat/inbox.html', context)

def thread_view(request):
	context = {}
	return render(request, 'chat/thread.html', context)

def new_message_view(request):
	context = {}
	return render(request, 'chat/new_message.html', context)
