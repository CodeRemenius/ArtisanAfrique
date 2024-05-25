from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from core.models import *
from core.forms import ProductForm
from core.models import Product, OrderItem, Order
from core.cart import Cart
from .auth_backends import EmailBackend
import json

def haggle_view(request):
    user_products = Product.objects.filter(user=request.user)
    haggles = Haggle.objects.filter(
        product__in=user_products,
        is_accepted=False,
        is_rejected=False
    )
    return render(request, 'userprofile/haggle.html', {'haggles': haggles})

def haggle_action(request, haggle_id):
    haggle = Haggle.objects.get(id=haggle_id)
    action = request.POST.get('action')

    if action == 'accept':
        haggle.is_accepted = True
        haggle.save()

        # Add the haggled product to the user's cart
        user_profile, _ = UserProfile.objects.get_or_create(user=haggle.user)
        cart_data = json.loads(user_profile.cart_data)  # Convert string to dictionary
        cart = Cart(request)

        # Use product ID as key for haggle object, and ensure it's passed as an integer
        product_id = haggle.product.id
        cart_data[product_id] = {
            'product_id': product_id,
            'quantity': 1,  # Assuming quantity is always 1 for accepted haggles
            'price': haggle.proposed_price  # Use proposed price as price in cart
        }
        user_profile.cart_data = json.dumps(cart_data)  # Convert dictionary to string
        user_profile.save()

        messages.success(request, 'Haggle accepted successfully.')
    elif action == 'decline':
        haggle.is_rejected = True
        haggle.save()
        messages.info(request, 'Haggle declined.')

    return redirect('haggle_view')

def haggle_history(request):
    user_products = Product.objects.filter(user=request.user)
    user_haggles = Haggle.objects.filter(product__in=user_products,is_accepted=True) | Haggle.objects.filter(product__in=user_products,is_rejected=True)

    return render(request, 'userprofile/haggle_history.html', {'haggles': user_haggles})

#Sign Up functionality
def signup(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        username = request.POST.get('shopName')
        password = request.POST.get('password')

        try:
            # Create a new user using Django's authentication system
            user = User.objects.create_user(username=username, email=email, password=password)

            # Create a UserProfile object linked to the user
            user_profile = UserProfile.objects.create(
                user=user,
                fullname=fullname,
                email=email,
                phone=phone,
                address=address,
                username=username,
                password=password,
                is_vendor=True
            )

            # Redirect to the login page
            return redirect('login_vendor')

        except IntegrityError:
            # Handle case where username already exists
            return render(request, 'userprofile/signup.html', {'error_message': 'Shop Name already exists'})

    return render(request, 'userprofile/signup.html')

#Login Functionality
def login(request):
    # check if form is using method of POST
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        email_backend = EmailBackend()

        # Authenticate user using email
        user = email_backend.check(request, email=email, password=password)
        
        if user is not None:
            try:
                # Check if the user is a vendor
                profile = UserProfile.objects.get(email=email)
                if profile.is_vendor:
                    # Login user and redirect to home page for vendors
                    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    return redirect('my_store')
                else:
                    # Return suitable error message for non-vendors
                    return render(request, 'userprofile/login.html', {'error_message': 'You are not authorized to access this page.'})
            except ObjectDoesNotExist:
                # Return suitable error message if UserProfile does not exist
                return render(request, 'userprofile/login.html', {'error_message': 'Invalid username or password.'})
        else:
            # User authentication failed, show error message
            return render(request, 'userprofile/login.html', {'error_message': 'Invalid email or password.'})

    return render(request, 'userprofile/login.html')

@login_required
def my_store(request):
    products = request.user.products.exclude(status=Product.DELETED)
    
    # Filter the order items to get those associated with the current user
    order_items = OrderItem.objects.filter(product__user=request.user)
    
    # Get the last 5 order items
    last_5_order_items = order_items.order_by('-order__created_at')[:5]

    # Fetch haggled prices for products with accepted haggles
    haggled_prices = {}
    accepted_haggles = Haggle.objects.filter(is_accepted=True)
    for haggle in accepted_haggles:
        # Filter order items associated with the current user and the product of the haggle
        matched_order_items = order_items.filter(product_id=haggle.product_id, order__created_by=haggle.user)
        if matched_order_items.exists():
            # Get the latest order item associated with the haggle
            order_item = matched_order_items.latest('order__created_at')
            # Use the haggle price for this order item
            haggled_prices[order_item.id] = haggle.proposed_price

    # Update order items with haggled prices
    for order_item in last_5_order_items:
        # Check if there is a haggled price for this order item
        if order_item.id in haggled_prices:
            # Use the haggled price multiplied by the quantity
            order_item.haggled_price = haggled_prices[order_item.id] * order_item.quantity
        else:
            # Use the original price multiplied by the quantity
            order_item.haggled_price = order_item.price * order_item.quantity

    return render(request, 'userprofile/dashboard.html', {
        'products': products,
        'order_items': last_5_order_items
    })

@login_required
def my_store_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    return render(request, 'userprofile/order_detail.html', {
        'order': order
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            title = request.POST.get('title')

            product = form.save(commit=False)
            product.user = request.user
            product.slug = slugify(title)
            product.save()

            messages.success(request, 'The product was added!')

            return redirect('my_store')
    else:
        form = ProductForm()

    return render(request, 'userprofile/product.html', {
        'title': 'Add product',
        'form': form
    })

@login_required
def edit_product(request, pk):
    product = Product.objects.filter(user=request.user).get(pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            form.save()

            messages.success(request, 'The changes was saved!')

            return redirect('my_store')
    else:
        form = ProductForm(instance=product)

    return render(request, 'userprofile/product.html', {
        'title': 'Edit product',
        'product': product,
        'form': form
    })

@login_required
def delete_product(request, pk):
    product = Product.objects.filter(user=request.user).get(pk=pk)
    product.status = Product.DELETED
    product.save()

    messages.success(request, 'The product was deleted!')

    return redirect('my_store')

@login_required
def my_products(request):
    products = Product.objects.filter(user=request.user)
    return render(request, 'userprofile/product_list.html', {'products': products})

@login_required
def my_orders(request):
    order_items = OrderItem.objects.filter(product__user=request.user, is_delivered=False)

    if request.method == 'POST':
        if 'delete_order_item' in request.POST:
            order_item_id = request.POST['delete_order_item']
            order_item = OrderItem.objects.get(id=order_item_id)
            order = order_item.order
            order_item.delete()
            if not order.items.exists():
                order.delete()
            return redirect('my_orders')

        if 'mark_delivered' in request.POST:
            order_item_id = request.POST['mark_delivered']
            order_item = OrderItem.objects.get(id=order_item_id)
            order = order_item.order
            order_item.is_delivered = True
            order_item.save()
            
            if order.items.count() == 1:  # Only one item in the order
                order.is_completed = True
            else:
                # Check if all items in the order are delivered
                if order.items.filter(is_delivered=False).exists():
                    order.is_completed = False
                else:
                    order.is_completed = True
            
            order.save()
            return redirect('my_orders')

    return render(request, 'userprofile/ordered_items.html', {'order_items': order_items})


@login_required
def deal_history(request):
    # Filter order items associated with the current user and are delivered
    order_items = OrderItem.objects.filter(product__user=request.user, is_delivered=True)

    # Fetch haggled prices for products with accepted haggles
    haggled_prices = {}
    accepted_haggles = Haggle.objects.filter(is_accepted=True)
    for haggle in accepted_haggles:
        # Filter order items associated with the current user and the product of the haggle
        matched_order_items = order_items.filter(product_id=haggle.product_id, order__created_by=haggle.user)
        if matched_order_items.exists():
            # Get the latest order item associated with the haggle
            order_item = matched_order_items.latest('order__created_at')
            # Use the haggle price for this order item
            haggled_prices[order_item.id] = haggle.proposed_price

    # Update order items with haggled prices
    for order_item in order_items:
        # Check if there is a haggled price for this order item
        if order_item.id in haggled_prices:
            # Use the haggled price multiplied by the quantity
            order_item.haggled_price = haggled_prices[order_item.id] * order_item.quantity
        else:
            # Use the original price multiplied by the quantity
            order_item.haggled_price = order_item.price * order_item.quantity

    return render(request, 'userprofile/deal_history.html', {'order_items': order_items})

@login_required
def my_chats(request, vendor_username):
    # Fetch the specified vendor
    vendor = get_object_or_404(User, username=vendor_username)

    # Fetch the last message from each unique sender to the vendor
    last_messages = {}
    chats = Message.objects.filter(receiver=vendor).order_by('-timestamp')
    for chat in chats:
        if chat.sender.username not in last_messages:
            last_messages[chat.sender.username] = chat

    # Create a list of dictionaries containing sender usernames and chat URLs
    chat_data = []
    for sender_username, chat in last_messages.items():
        chat_url = reverse('chat_vendor', kwargs={'user1_username': vendor_username, 'user2_username': sender_username})
        chat_data.append({'sender_username': sender_username, 'chat_url': chat_url})

    return render(request, 'userprofile/my_chats.html', {'vendor_username': vendor_username, 'chat_data': chat_data})

@login_required
def chat_page(request, user1_username, user2_username):
    # Fetch the authenticated user (vendor)
    vendor = request.user

    # Fetch the receiver (user whose link was clicked)
    user2 = get_object_or_404(User, username=user2_username)

    # Fetch only the last 5 messages between the vendor and the user
    messages = Message.objects.filter(sender=vendor, receiver=user2) | Message.objects.filter(sender=user2, receiver=vendor)
    messages = messages.order_by('-timestamp')[:5]  # Select the last 5 messages

    # Reverse the message list so that the latest message appears at the bottom in the chat window
    messages = reversed(messages)

    # Handle message sending and receiving logic here
    if request.method == 'POST':
        message_text = request.POST.get('message-input')  # Update here to match the input field's ID
        # Create a new message object and save it
        Message.objects.create(sender=vendor, receiver=user2, text=message_text)

        # Redirect to the same page to prevent form resubmission
        return redirect('chat_vendor', user1_username=user1_username, user2_username=user2_username)

    return render(request, 'userprofile/chat.html', {'user1': vendor, 'user2': user2, 'messages': messages})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login_vendor')  # Redirect to the vendor login page after logout

@login_required
def edit_profile(request):
    # Retrieve the user's UserProfile instance
    user_profile = request.user.userprofile
    user = request.user

    if request.method == 'POST':
        # Extract data from the POST request
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        profile_picture = request.FILES.get('profile_picture')

        user.username = username
        user.email = email
        user.save()

        # Update the UserProfile instance with the new data
        user_profile.fullname = fullname
        user_profile.email = email
        user_profile.phone = phone
        user_profile.address = address
        if profile_picture:
            user_profile.profile_picture = profile_picture

        # Save the changes to the UserProfile instance
        user_profile.save()

        # Display a success message
        messages.success(request, 'Profile updated successfully.')

        # Redirect back to the edit profile page
        return redirect('edit_profile')

    # Render the edit profile page with the UserProfile data
    return render(request, 'userprofile/edit_profile.html', {'user_profile': user_profile})
