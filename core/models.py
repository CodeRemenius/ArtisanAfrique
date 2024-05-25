from django.db import models
from django.utils import timezone
from statistics import mode
from django.contrib.auth.models import User
from django.db import models
from django.core.files import File

from io import BytesIO
from PIL import Image

class Category(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)

    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.title

class Product(models.Model):
    DRAFT = 'draft'
    WAITING_APPROVAL = 'waitingapproval'
    ACTIVE = 'active'
    DELETED = 'deleted'

    STATUS_CHOICES = (
        (DRAFT, 'Draft'),
        (WAITING_APPROVAL, 'Waiting approval'),
        (ACTIVE, 'Active'),
        (DELETED, 'Deleted'),
    )

    user = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    image = models.ImageField(upload_to='uploads/product_images', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/product_images/thumbnail', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=ACTIVE)

    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return self.title
    
    def get_display_price(self):
        # Convert price to string and reverse it
        price_str = str(self.price)[::-1]

        # Add commas after every three digits
        formatted_price = ",".join([price_str[i:i+3] for i in range(0, len(price_str), 3)])

        # Reverse the string again to get the original order
        return formatted_price[::-1]

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            if self.image:
                self.thumbnail = self.make_thumbnail(self.image)
                self.save()

                return self.thumbnail.url
            else:
                return 'https://via.placeholder.com/240x240x.jpg'
    
    def make_thumbnail(self, image, size=(300, 300)):
        img = Image.open(image)
        img.convert('RGB')
        img.thumbnail(size)

        thumb_io = BytesIO()
        img.save(thumb_io, 'JPEG', quality=85)
        name = image.name.replace('uploads/product_images/', '')
        thumbnail = File(thumb_io, name=name)

        return thumbnail

class Order(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    paid_amount = models.IntegerField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='orders', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    date_completed = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.is_completed:
            self.date_completed = timezone.now()
        super().save(*args, **kwargs)


    def __str__(self):
        return f'Order {self.pk} - {self.first_name} {self.last_name}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='items', on_delete=models.CASCADE)
    price = models.IntegerField()
    quantity = models.IntegerField(default=1)
    is_delivered = models.BooleanField(default=False)

    @property
    def total_cost(self):
        return self.price * self.quantity
  
    def get_display_price(self):
        return self.price

    def get_new_display(self):
        price = self.price * self.quantity
        total_cost_str = str(price)[::-1]

        # Add commas after every three digits
        formatted_cost = ",".join([total_cost_str[i:i+3] for i in range(0, len(total_cost_str), 3)])

        # Reverse the string again to get the original order
        return formatted_cost[::-1]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='media/', null=True, blank=True)
    is_vendor = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    cart_data = models.TextField(default='{}')  # Field to store serialized cart data

    def __str__(self):
        return self.username

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

class Haggle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    proposed_price = models.IntegerField()
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)  # Optional, can be null initially

    def save(self, *args, **kwargs):
        if self.is_accepted or self.is_rejected:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.product.title} - NGN {self.proposed_price}"