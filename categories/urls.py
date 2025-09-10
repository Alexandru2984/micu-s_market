from django.urls import path
from .views import subcategory_detail_view
from .views import category_detail_view
from .views import category_list_view

urlpatterns = [

	path("category_list", category_list_view),
	path("category_detail", category_detail_view),
	path("subcategory_detail", subcategory_detail_view),
]
