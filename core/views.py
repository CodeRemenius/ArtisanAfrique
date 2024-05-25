from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q,F
from django.shortcuts import render,redirect,get_object_or_404
from django.urls import reverse
from userprofile.auth_backends import EmailBackend
from .models import *
from .cart import Cart

#Login And Sign Up related
def signup(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        username = request.POST.get('signupUsername')
        password = request.POST.get('signupPassword')

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
                is_customer=True

            )

            # Redirect to the login page
            return redirect('login')

        except IntegrityError:
            # Handle case where username already exists
            return render(request, 'core/signUp.html', {'error_message': 'Username already exists'})

    return render(request, 'core/signUp.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        email_backend = EmailBackend()

        # Authenticate user using username
        user = email_backend.authenticate(request,username=username, password=password)
        print(user)

        if user is not None:
            # Check if the user is a vendor
            try:
                profile = UserProfile.objects.get(user=user)
                if not profile.is_customer:
                    return render(request, 'core/login.html', {'error_message': 'Vendor login not allowed'})
            except UserProfile.DoesNotExist:
                pass

            # Login user and redirect to home page
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Associate the cart with the user if authenticated
            if request.user.is_authenticated:
                cart = Cart(request)
                cart.save()

            return redirect('home')
        else:
            # User authentication failed, show error message
            return render(request, 'core/login.html', {'error_message': 'Username or Password Incorrect'})

    return render(request, 'core/login.html')

#Home page
def home(request):
    products = Product.objects.filter(status=Product.ACTIVE)[0:6]
    user = request.user
    return render(request, 'core/home.html', {
        'products': products,
        'user': user
    })

def about(request):
    return render(request, 'core/about.html')


def success(request):
    return render(request, 'core/success.html')

def change_quantity(request, product_id):
    action = request.GET.get('action', '')

    if action:
        quantity = 1

        if action == 'decrease':
            quantity = -1

        cart = Cart(request)
        cart.add(product_id, quantity, True)
    
    return redirect('cart_view')

def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)

    return redirect('cart_view')

def cart_view(request):
    cart = Cart(request)

    return render(request, 'core/cart_view.html', {
        'cart': cart
    })

def search(request):
    query = request.GET.get('query', '')

    # Search for products
    products = Product.objects.filter(status=Product.ACTIVE).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )

    # Search for vendors
    vendors = UserProfile.objects.filter(
        Q(fullname__icontains=query) | Q(username__icontains=query)
    )

    return render(request, 'core/search.html', {
        'query': query,
        'products': products,
        'vendors': vendors,
    })

#Detail Page
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(status=Product.ACTIVE)

    return render(request, 'core/category_detail.html', {
        'category': category,
        'products': products
    })

def product_detail(request, category_slug, slug):
    product = get_object_or_404(Product, slug=slug, status=Product.ACTIVE)

    return render(request, 'core/product_detail.html', {
        'product': product
    })


def add_to_cart(request, product_id):
    cart = Cart(request)
    cart.add(int(product_id))  # Convert product_id to integer

    return redirect('cart_view')
    
def vendor_detail(request, username):
    user_profile = get_object_or_404(UserProfile, username=username)
    
    products = Product.objects.filter(user=user_profile.user, status=Product.ACTIVE)
    
    return render(request, 'core/vendor_detail.html', {
        'user_profile': user_profile,
        'products': products,
    })

@login_required
def checkout(request):
    cart = Cart(request)

    if cart.get_total_cost() == 0:
        return redirect('cart_view')

    # Calculate total amount
    total_amount = cart.get_total_cost()

    # Pre-fill order form with user's information
    user_profile = UserProfile.objects.get(user=request.user)
    initial_data = {
        'first_name': user_profile.user.first_name,
        'last_name': user_profile.user.last_name,
        'address': user_profile.address,
    }

    if request.method == 'POST':
        # Extract form data directly from request.POST
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')

        # Create the order with the extracted form data
        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            address=address,
            paid_amount=total_amount,  # Fill paid_amount with total amount
            created_by=request.user,
            is_paid=True  # Assuming payment successful without Stripe
        )

        # Create order items here
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            price = product.price  # Get the price from the product
            OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)

        cart.clear()

        return render(request, 'core/success.html')  # Redirect to payment successful page

    # Render the checkout page with the pre-filled form data
    return render(request, 'core/checkout.html', {
        'cart': cart,
        'initial_data': initial_data,
        'total_amount': total_amount,  # Pass total amount to template
    })

@login_required
def chat_page(request, user1_username, user2_username):
    # Fetch user objects for user1 and user2
    user1 = get_object_or_404(User, username=user1_username)
    user2 = get_object_or_404(User, username=user2_username)
    
    # Fetch only the last 5 messages between user1 and user2
    messages = Message.objects.filter(sender=user1, receiver=user2) | Message.objects.filter(sender=user2, receiver=user1)
    messages = messages.order_by('-timestamp')[:5]  # Select the last 5 messages
    
    # Reverse the message list so that the latest message appears at the bottom in the chat window
    messages = reversed(messages)
    
    # Handle message sending and receiving logic here
    if request.method == 'POST':
        message_text = request.POST.get('message-input')  # Update here to match the input field's ID
        # Create a new message object and save it
        Message.objects.create(sender=user1, receiver=user2, text=message_text)

        # Redirect to the same page to prevent form resubmission
        return redirect('chat_page', user1_username=user1_username, user2_username=user2_username)
    
    return render(request, 'core/chat.html', {'user1': user1, 'user2': user2, 'messages': messages})

@login_required
def my_chats(request):
    # Fetch the active user
    active_user = request.user

    # Fetch all unique vendors the active user has conversed with
    vendors = User.objects.filter(received_messages__sender=active_user).distinct()

    # Create a list of dictionaries containing vendor usernames and chat URLs
    chat_data = []
    for vendor in vendors:
        # Fetch the last message from the active user to each vendor
        last_message = Message.objects.filter(sender=active_user, receiver=vendor).order_by('-timestamp').first()
        if last_message:
            chat_url = reverse('chat_page', kwargs={'user1_username': active_user.username, 'user2_username': vendor.username})
            chat_data.append({'vendor_username': vendor.username, 'chat_url': chat_url})

    return render(request, 'core/my_chats.html', {'chat_data': chat_data})

def monitor_orders(request):
    # Fetch orders that are not completed and are created by the logged-in user
    orders = Order.objects.filter(created_by=request.user)

    return render(request, 'core/monitor_orders.html', {'orders': orders})

@login_required
def haggle(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    
    if request.method == 'POST':
        proposed_price = request.POST.get('proposed_price')
        haggle = Haggle.objects.create(user=request.user, product=product, proposed_price=proposed_price)
        return redirect('product_detail', category_slug=product.category.slug, slug=product.slug)

    return render(request, 'core/haggle.html', {'product': product})
    
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def edit_profile(request):
    # Retrieve the user's UserProfile instance
    user_profile = request.user.userprofile
    user = request.user

    if request.method == 'POST':
        # Extract data from the POST request
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        profile_picture = request.FILES.get('profile_picture')

        user.username = username
        user.email = email
        user.save()

        # Update the UserProfile instance with the new data
        user_profile.username = username
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
    return render(request, 'core/edit_profile.html', {'user_profile': user_profile})

def haggle_history(request):
    # Retrieve all haggles made by the current user
    haggles = Haggle.objects.filter(user=request.user)

    return render(request, 'core/haggle_history.html', {'haggles': haggles})


def change_password_page1(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        if user is not None:
            return redirect('change_password_page2')
        else:
            return render(request, 'core/change_password_page.html', {'error_message': 'Incorrect password'})
    return render(request, 'core/change_password_page.html')

def change_password_page2(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')
        if new_password == confirm_new_password:
            user = User.objects.get(username=request.user.username)
            user.set_password(new_password)
            user.save()
            user_profile = UserProfile.objects.get(user=user)
            user_profile.password = new_password
            user_profile.save()
            return redirect('change_password_success')
        else:
            return render(request, 'core/confirm_password_page.html', {'error_message': 'Passwords do not match'})
    return render(request, 'core/confirm_password_page.html')

def change_password_success(request):
    return render(request, 'core/password_change_success.html')