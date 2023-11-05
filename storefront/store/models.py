from uuid import uuid4

from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

from .validators import validate_file_size

# Create your models here.


class Promotion(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название', default=None)
    description = models.CharField(max_length=255, verbose_name='Описание', null=True, blank=True, default=None)
    discount = models.FloatField(validators=[MinValueValidator(0)], verbose_name='Процент скидки')

    def __str__(self):
        return f'{self.title} {self.discount}'

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'

class Collection(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название категории')


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['title']



class Product(models.Model):
    title = models.CharField(max_length=50, verbose_name='Наименование товара')
    slug = models.SlugField()
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(1)],
                                verbose_name='Цена')

    inventory = models.IntegerField(validators=[MinValueValidator(0)],
                                    verbose_name='Кол-во на складе')

    last_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT,
                                   verbose_name='Категория', related_name='products')

    # promotion = models.ManyToManyField(Promotion, blank=True)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Акции')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['title']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='store/images', validators=[validate_file_size])

class Customer(models.Model):
    # Статусы покупателей
    MEMBERSHIP_BRONZE = 'B'
    MEMBERSHIP_SILVER = 'S'
    MEMBERSHIP_GOLD = 'G'

    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, 'Bronze'),
        (MEMBERSHIP_SILVER, 'Silver'),
        (MEMBERSHIP_GOLD, 'Gold')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                default=None)

    phone = models.CharField(max_length=50, verbose_name='Номер телефона')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    membership = models.CharField(max_length=1, choices=MEMBERSHIP_CHOICES,
                                  default=MEMBERSHIP_BRONZE, verbose_name='Статус')

    def __str__(self):
        return f'{self.user}'

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Корзина',
                             related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Количество товаров')

    def __str__(self):
        return self.product.title

    class Meta:
        unique_together = [['cart', 'product']]


class Order(models.Model):
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
    ]

    placed_at = models.DateTimeField(auto_now_add=True, verbose_name='Время оформления')
    payment_status = models.CharField(max_length=1, choices=PAYMENT_STATUS_CHOICES,
                                      default=PAYMENT_STATUS_PENDING,
                                      verbose_name='Статус оплаты')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name='Покупатель')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Кол-во заказанного')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')



class Address(models.Model):
    street = models.CharField(max_length=50, verbose_name='Улица')
    city = models.CharField(max_length=50, verbose_name='Город')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                 verbose_name='Покупатель')


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Товар', related_name='reviews')
    customer_id = models.IntegerField(default=0, verbose_name='id покупателя')
    name = models.CharField(max_length=50)
    description = models.TextField(verbose_name='Описание')
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'