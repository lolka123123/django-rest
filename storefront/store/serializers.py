from rest_framework import serializers
from .models import Product, Collection, Review, CartItem, Cart, Customer, Order, OrderItem, ProductImage, Promotion
from decimal import Decimal
from django.db import transaction
from .signals import order_created

from tags.models import Tag, TaggedItem
from likes.models import LikedItem



class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ['id', 'title', 'description', 'discount']


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'product_count']

    product_count = serializers.IntegerField(read_only=True)


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'date', 'description']

    def create(self, validated_data):
        product_id = self.context['product_id']
        customer_id = self.context['customer_id']
        return Review.objects.create(product_id=product_id, customer_id=customer_id, **validated_data)

class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id, **validated_data)

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'price_with_discount', 'price_with_tax', 'description',
                  'slug', 'inventory', 'images', 'collection', 'promotion', 'reviews']

    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')
    price_with_discount = serializers.SerializerMethodField(method_name='calculate_discount')
    collection = CollectionSerializer()
    reviews = ReviewSerializer(many=True)
    promotion = PromotionSerializer()
    # price = serializers.SerializerMethodField(method_name='price_with_discount')
    # price_without_discount = serializers.SerializerMethodField(method_name='get_price_without_discount')



    # def get_price_without_discount(self, product):
    #     return product.price
    def calculate_discount(self, product):
        if product.promotion:
            price = float(product.price)
            discount = product.promotion.discount
            # return round(float(product.price) - (float(product.price) * product.promotion.discount))
            return price - (price * discount)
        return product.price

    def calculate_tax(self, product):
        return round(product.price * Decimal(1.1), 2)

    def create(self, validated_data):
        product = Product(**validated_data)
        product.other = 1
        product.save()
        return product

    def update(self, instance, validated_data):
        instance.price = validated_data.get('price')
        instance.save()
        return instance

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'price_with_discount', 'inventory', 'promotion']

    promotion = PromotionSerializer()

    price_with_discount = serializers.SerializerMethodField(method_name='calculate_discount')


    def calculate_discount(self, product):
        if product.promotion:
            # return round(float(product.price) - (float(product.price) * product.promotion.discount))
            price = float(product.price)
            discount = product.promotion.discount
            return price - (price * discount)
        return product.price

    #
    # def price_with_discount(self, product):
    #     if product.promotion:
    #         return round(float(product.price) - (float(product.price) * product.promotion.discount))
    #     return product.price


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    def get_total_price(self, cart_item: CartItem):
        if cart_item.product.promotion:
            price = float(cart_item.product.price)
            discount = cart_item.product.promotion.discount
            return cart_item.quantity * (price - price * discount)
        return cart_item.quantity * cart_item.product.price

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    def get_total_price(self, cart: Cart):

        # return sum(item.quantity * item.product.price for item in cart.items.all())

        lst = []
        for item in cart.items.all():
            if item.product.promotion:
                price = float(item.product.price)
                discount = item.product.promotion.discount
                lst.append(float(price - price * discount) * float(item.quantity))
            else:
                lst.append(float(item.product.price))
        return sum(lst)


    class Meta:
        model = Cart
        fields = ['id', 'total_price', 'items']


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Нет товара с данным id')
        return value

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        if quantity == 0:
            raise serializers.ValidationError('Нельзя добавить 0 товаров')

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)

            if (cart_item.quantity + quantity) < 0:
                cart_item.quantity = 0
            else:
                cart_item.quantity += quantity

            cart_item.save()

            # if cart_item.quantity <= 0:
            #     cart_item.delete()

            self.instance = cart_item

        except:
            if self.validated_data['quantity'] < 0:
                self.validated_data['quantity'] = 0
            cart_item = CartItem.objects.create(cart_id=cart_id, **self.validated_data)

            # if cart_item.quantity <= 0:
            #     cart_item.delete()
            self.instance = cart_item

        return self.instance

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class UpdateCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'membership']
        read_only_fields = ['membership']

class AdminCustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'membership']







class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    def get_total_price(self, order_item):
        return order_item.quantity * order_item.price

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')


    def get_total_price(self, order):
        return sum(item.quantity * item.price for item in order.items.all())


    class Meta:
        model = Order
        fields = ['id', 'customer', 'placed_at', 'payment_status', 'total_price', 'items']

class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']

class CreateOrderSerializer(serializers.ModelSerializer):
    cart_id = serializers.UUIDField()
    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('Не существующий ID корзины')
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('Корзина пустая')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer = Customer.objects.get(user_id=self.context['user_id'])
            order = Order.objects.create(customer=customer)

            cart_items = CartItem.objects.select_related('product').filter(cart_id=cart_id)

            error_items = ''
            for item in cart_items:
                if item.quantity > item.product.inventory:
                    error_items += f'{item}({item.quantity-item.product.inventory}), '

            if error_items != '':
                raise serializers.ValidationError(f'Недостаточно товаров на складе: {error_items}')

            # with open('lol.txt', mode='a', encoding='UTF-8') as data:
            #     data.write(f'{item}({item.quantity - item.product.inventory})\n')




            for item in cart_items:
                if item.product.promotion:
                    price = float(item.product.price) - (float(item.product.price) * item.product.promotion.discount)
                else:
                    price = float(item.product.price)
                OrderItem.objects.create(order=order, product=item.product,
                                         quantity=item.quantity, price=price)

                product = Product.objects.get(id=item.product.id)
                product.inventory -= item.quantity
                product.save()


            Cart.objects.filter(pk=cart_id).delete()

            order_created.send_robust(self.__class__, order=order)
            return order

    class Meta:
        model = Order
        fields = ['id', 'cart_id']
        # , 'customer', 'payment_status', 'placed_at'


class LikedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedItem
        fields = ['id', 'user', 'content_type', 'object_id']

    user = serializers.ReadOnlyField(source='user.id')



    def save(self, **kwargs):
        request = self.context['request']
        liked_item = LikedItem.objects.create(user=request.user, **self.validated_data)

        return liked_item

    # def create(self, validated_data):
    #     request = self.context['request']
    #     LikedItem.objects.create(user=request.user, **validated_data)




class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'label']

class TaggedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaggedItem
        fields = ['id', 'tag', 'content_type', 'object_id', 'objects']





# class TestAddCollectionSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = Collection
#         fields = ['id', 'title']