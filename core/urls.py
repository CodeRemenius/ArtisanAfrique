from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views 

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),    
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'), path('sign-up/', views.signup, name="sign_up"),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('monitor/', views.monitor_orders, name='monitor_orders'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('change-quantity/<str:product_id>/', views.change_quantity, name='change_quantity'),
    path('remove-from-cart/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/success/', views.success, name='success'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('my-chats/', views.my_chats, name='my_chats'),
    path('change-password/', views.change_password_page1, name='change_password_page1'),
    path('change-password/confirm/', views.change_password_page2, name='change_password_page2'),
    path('change-password/success/', views.change_password_success, name='change_password_success'),
    path('haggle-history/', views.haggle_history, name='haggle_history'),
    path('vendor/<str:username>/', views.vendor_detail, name='vendor_detail'),
    path('haggle/<slug:product_slug>/', views.haggle, name='haggle'),
    path('<slug:slug>/', views.category_detail, name='category_detail'),
    path('<slug:category_slug>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('chat/<str:user1_username>/<str:user2_username>/', views.chat_page, name='chat_page'),
]
