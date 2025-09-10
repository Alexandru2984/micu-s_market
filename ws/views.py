from django.shortcuts import render

# Create your views here.

def chat_room_view(request):
	context = {}
	return render(request, 'ws/chat_room.html', context)

def notifications_stream_view(request):
	context = {}
	return render(request, 'ws/notifications_stream.html', context)
