from django.urls import path
from . import views
from rest_framework_nested import routers

# urlpatterns = [
#     path('product/', views.ProductList.as_view(), name='product_list'),
#     path('product/<int:pk>', views.ProductDetail.as_view(), name='product_detail'),
#     path('collection/', views.CollectionList.as_view(), name='collection_list'),
#     path('collection/<int:pk>', views.CollectionDetail.as_view(), name='collection_detail'),
# ]

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='products')
router.register('collections', views.CollectionViewSet, basename='collections')
router.register('carts', views.CartViewSet)
router.register('customers', views.CustomerViewSet)
router.register('orders', views.OrderViewSet, basename='orders')
router.register('promotions', views.PromotionViewSet, basename='promotions')


router.register('liked_items', views.LikedItemViewSet, basename='liked_item')
router.register('tags', views.TagViewSet, basename='tags')
router.register('tagged_items', views.TaggedItemItemViewSet, basename='tagged_items')




product_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
product_router.register('reviews', views.ReviewViewSet, basename='product-reviews')

carts_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
carts_router.register('items', views.CartItemViewSet, basename='cart-items')



add_products = [path('test_add_products/', views.add_products, name='test_add_products')]

urlpatterns = router.urls + product_router.urls + carts_router.urls + add_products