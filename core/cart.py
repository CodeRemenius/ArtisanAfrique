from django.conf import settings
from .models import *
import json


class Cart(object):
    def __init__(self, request):
        self.request = request

        if request.user.is_authenticated:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            self.cart = json.loads(user_profile.cart_data)
        else:
            self.cart = json.loads(request.session.get(settings.CART_SESSION_ID, '{}'))

    def __iter__(self):
        for p in self.cart.keys():
            self.cart[str(p)]['product'] = Product.objects.get(pk=p)
        
        for item in self.cart.values():
            # Update the total price based on haggled price if available
            if 'price' in item:
                item['total_price'] = item['price'] * item['quantity']
            else:
                item['total_price'] = item['product'].price * item['quantity']

            yield item
    
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def save(self):
        if self.request.user.is_authenticated:
            user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            user_profile.cart_data = json.dumps(self.cart)
            user_profile.save()
        else:
            self.request.session[settings.CART_SESSION_ID] = json.dumps(self.cart)
            self.request.session.modified = True

    def add(self, product_id, quantity=1, update_quantity=False):
        product_id = str(product_id)

        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': int(quantity), 'id': product_id}
        
        if update_quantity:
            self.cart[product_id]['quantity'] += int(quantity)
            
            if self.cart[product_id]['quantity'] == 0:
                self.remove(product_id)
        
        self.save()
    
    def remove(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]

            self.save()
    
    def clear(self):
        if self.request.user.is_authenticated:
            user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            user_profile.cart_data = json.dumps({})
            user_profile.save()
        else:
            self.request.session[settings.CART_SESSION_ID] = json.dumps({})
            self.request.session.modified = True

    def get_total_cost(self):
        total_cost = 0
        for p in self.cart.keys():
            self.cart[str(p)]['product'] = Product.objects.get(pk=p)
            if 'price' in self.cart[str(p)]:
                total_cost += self.cart[str(p)]['price'] * self.cart[str(p)]['quantity']
            else:
                total_cost += self.cart[str(p)]['product'].price * self.cart[str(p)]['quantity']
        
        return total_cost
    
    def get_display_price(self):
        # Convert total cost to string and reverse it
        total_cost_str = str(self.get_total_cost())[::-1]

        # Add commas after every three digits
        formatted_cost = ",".join([total_cost_str[i:i+3] for i in range(0, len(total_cost_str), 3)])

        # Reverse the string again to get the original order
        return formatted_cost[::-1]
