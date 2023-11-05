from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import Product, Collection, OrderItem, Review, Cart, CartItem, Customer, Order, Promotion
from django.http import HttpResponse


from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer, CollectionSerializer, ReviewSerializer, \
    CartSerializer, CartItemSerializer, AddCartItemSerializer, UpdateCartSerializer, \
    CustomerSerializer, OrderSerializer, UpdateOrderSerializer, CreateOrderSerializer, \
    PromotionSerializer, LikedItemSerializer, TagSerializer, TaggedItemSerializer, \
    AdminCustomerSerializer

#     , LikedItemSerializer, TagSerializer, TaggedItemSerializer


from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from .pagination import DefaultPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter

from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin, CreateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action

from .permissions import IsAdminOrReadOnly, IsAdminOrPost, IsAdminOrOwner

from tags.models import Tag, TaggedItem
from likes.models import LikedItem

from rest_framework.renderers import TemplateHTMLRenderer

class CollectionViewSet(ModelViewSet):
    serializer_class = CollectionSerializer
    queryset = Collection.objects.annotate(products_count=Count('products')).all()

    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=self.kwargs['pk']).count() > 0:
            return Response({'error': 'Категория не может быть удалена.'
                                      'Так как есть в ней товары'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(self, request, *args, **kwargs)

class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    pagination_class = DefaultPagination
    # filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'last_update']

    permission_classes = [IsAdminOrReadOnly]

    # renderer_classes = [TemplateHTMLRenderer]
    # template_name = 'index.html'



    def get_queryset(self):
        queryset = Product.objects.all()
        collection_id = self.request.query_params.get('collection_id')
        if collection_id is not None:
            queryset = queryset.filter(collection_id=collection_id)
        return queryset

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=self.kwargs['pk']).count() > 0:
            return Response({'error': 'Товар не может быть удален. Так как есть в заказах'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(self, request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer


    def get_permissions(self):
        if self.request.user.is_authenticated:
            try:
                customer_id = Customer.objects.get(user_id=self.request.user.id).id
                if Review.objects.filter(id=self.kwargs['pk'],
                                         product_id=self.kwargs['product_pk'],
                                         customer_id=customer_id).exists():
                    return [IsAdminOrOwner()]
                return [IsAdminOrPost()]
            except:
                return [IsAdminOrPost()]
        return [IsAdminOrPost()]


    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        try:
            customer_id = Customer.objects.get(user_id=self.request.user.id).id
        except:
            customer_id = 0

        return {
            'customer_id': customer_id,
            'product_id': self.kwargs['product_pk']
        }





class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer

class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartSerializer

        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk']).select_related('product')


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrReadOnly]


    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminCustomerSerializer
        else:
            return CustomerSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Customer.objects.all()
        return Customer.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {
            'request': self.request
        }

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        try:
            customer = Customer.objects.get(user_id=request.user.id)
        except:
            customer, created = Customer.objects.get_or_create(user_id=request.user.id)

        if request.method == 'GET':
            if request.user.is_staff:
                serializer = AdminCustomerSerializer(customer)
            else:
                serializer = CustomerSerializer(customer)
            return Response(serializer.data)

        elif request.method == 'PUT':
            if request.user.is_staff:
                serializer = AdminCustomerSerializer(customer, data=request.data)
            else:
                serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'put', 'post', 'patch', 'delete', 'head', 'options']
    # queryset = Order.objects.all()

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Order.objects.all()

        customer_id = Customer.objects.only('id').get(user_id=user.id)
        return Order.objects.filter(customer_id=customer_id)




    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE', 'PUT', 'OPTIONS']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data,
                                           context={'user_id': request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        serializer = OrderSerializer(order)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PUT':
            return UpdateOrderSerializer
        return OrderSerializer


class PromotionViewSet(ModelViewSet):
    serializer_class = PromotionSerializer
    queryset = Promotion.objects.all()

    permission_classes = [IsAdminOrReadOnly]





class LikedItemViewSet(ModelViewSet):
    serializer_class = LikedItemSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return LikedItem.objects.all()
        return LikedItem.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.request.user.is_authenticated:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_serializer_context(self):
        return {'request': self.request}

class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    permission_classes = [IsAdminOrReadOnly]

class TaggedItemItemViewSet(ModelViewSet):
    serializer_class = TaggedItemSerializer
    queryset = TaggedItem.objects.all()

    permission_classes = [IsAdminOrReadOnly]




from rest_framework.decorators import api_view
from rest_framework.response import Response

import json


@api_view()
def add_products(request):
    with open('TexnomartParser.json', mode='r', encoding='UTF-8') as file:
        data = json.load(file)
        for key, value in data.items():
            Collection.objects.create(title=key)
            for product in value:
                title = product['Наименование товара']
                price = product['Цена товара']
                inventory = 100
                collection = Collection.objects.get(title=key)
                description = ''
                for description_key, description_value in product['Характеристики'].items():
                    description += f'{description_key}:\n'
                    for k, v in description_value.items():
                        description += f'\t{k}: {v}\n'

                Product.objects.create(title=title,
                                       description=description,
                                       price=price, inventory=inventory,
                                       collection=collection)

    return Response({'status': 'ok'})