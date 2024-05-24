from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.signup, name='register_vendor'),
    path('', views.login, name='login_vendor'),
    path('logout/', views.logout_view, name='logout_vendor'),
    path('my-store/', views.my_store, name='my_store'),
    path('my-products/', views.my_products, name='my_products'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-store/order-detail/<int:pk>/', views.my_store_order_detail, name='my_store_order_detail'),
    path('my-store/add-product/', views.add_product, name='add_product'),
    path('my-store/edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('my-store/delete-product/<int:pk>/', views.delete_product, name='delete_product'),
    path('haggles/', views.haggle_view, name='haggle_view'),
    path('haggle/<int:haggle_id>/', views.haggle_action, name='haggle_action'),
    path('haggle-history/', views.haggle_history, name='haggle_history_artisan'),
    path('edit-profile/', views.edit_profile, name='edit_profile_artisan'),
    path('chat/<str:user1_username>/<str:user2_username>/', views.chat_page, name='chat_vendor'),
    path('my-chats/<str:vendor_username>/', views.my_chats, name='my_chats'),
    path('deal-history/', views.deal_history, name='deal_history'),
]