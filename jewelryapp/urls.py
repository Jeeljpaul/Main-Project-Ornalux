from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .models import Vendor  # Import Vendor model

urlpatterns = [
    path('', views.index, name='home'),
    path('base_home/',views.base),
    path('login/',views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('adminhome/',views.adminhome, name='adminhome'),
    path('staffhome/',views.staffhome),
    path('register/',views.register, name='register'),
    path('forgot_password/', views.forgot_password),
    path('reset-password/<str:token>/', views.reset_password),
    path('social-auth/', include('social_django.urls', namespace='social')),

    # path('adminhome/add_p/', views.add_p, name='add_p'),
    path('adminhome/update_pro/<int:product_id>/', views.update_pro, name='update_pro'),  # New URL pattern
   
    # path('adminhome/add_product/', views.add_product, name='add_product'),
    path('adminhome/product_list/', views.product_list, name='product_list'),  # Make sure this line exists   
    path('adminhome/view_products/',views.view_products, name='view_products'),
    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    path('product/<int:product_id>/toggle_status/', views.toggle_product_status, name='toggle_product_status'),
    # path('product/<int:product_id>/update/', views.update_product, name='update_product'),

    path('adminhome/add-category/', views.add_category, name='add_category'),
    path('categories/', views.view_categories, name='view_categories'),
    path('add_attribute/<int:category_id>/', views.add_attribute_to_category, name='add_attribute_to_category'),


    path('get_category_attributes/<int:category_id>/', views.get_category_attributes, name='get_category_attributes'),
    path('adminhome/add_metaltype/', views.add_metaltype, name='add_metaltype'),
    path('view-metaltypes/', views.view_metaltypes, name='view_metaltypes'),
    path('adminhome/add_stonetype/', views.add_stonetype, name='add_stonetype'),
    path('view-stonetypes/', views.view_stonetypes, name='view_stonetypes'),
    path('adminhome/add_pro/', views.add_pro, name='add_pro'),


    path('view_registered_users/', views.view_registered_users, name='view_registered_users'),
    path('toggle_user_status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

    path('add_staff/', views.add_staff, name='add_staff'),
    path('view_staff/', views.view_staff, name='view_staff'),
    path('update_staff/<int:staff_id>/', views.update_staff, name='update_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),

    path('view_bookings/', views.view_bookings, name='view_bookings'),



    path('product/', views.product, name='product'),
    path('ring_list/', views.ring_lists, name='ring_list'),
    path('earring_list/', views.earring_list, name='earring_list'),
    path('bracelet_list/', views.bracelet_lists, name='bracelet_list'),
    path('ring_detail/<int:product_id>/', views.ring_detail, name='ring_detail'),
    path('earring/<int:product_id>/', views.earring_detail, name='earring_detail'),
    path('bracelet_detail/<int:product_id>/', views.bracelet_detail, name='bracelet_detail'),
    path('allproducts',views.all_products,name='allproducts'),
    path("search_suggestions/", views.search_suggestions, name="search_suggestions"),
    path('detail/<int:product_id>/', views.detail, name='detail'),
    path('book_schedule/<int:product_id>/', views.book_schedule, name='book_schedule'),
    path('submit_schedule/<int:product_id>/', views.submit_schedule, name='submit_schedule'),
    path('booking-details/<int:booking_id>/', views.booking_details, name='booking_details'),

    path('booking_history/', views.booking_history, name='booking_history'),
    path('edit_booking/<int:booking_id>/', views.edit_booking, name='edit_booking'),



    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('update_cart_quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove_item_from_cart/', views.remove_item_from_cart, name='remove_item_from_cart'),
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('remove_from_wishlist/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # path('checkout/', views.checkout, name='checkout'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('addresses/', views.address_view, name='address_view'),
    path('select_address/', views.select_address, name='select_address'),
    path('add_address/', views.add_address, name='add_address'),
    path('order-summary/', views.order_summary, name='order_summary'),

    path('order_history/', views.order_history, name='order_history'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),


    path('profile/', views.profile, name='profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('staffhome', views.staffhome, name='staffhome'),
    path('staff/accept-booking/<int:booking_id>/', views.accept_booking, name='accept_booking'),

    path('gold-exchange/', views.gold_exchange_page, name='gold_exchange'),
    path('gold_rates/', views.gold_rates_view, name='gold_rates'),
    path('calculate_gold_value/', views.calculate_gold_value, name='calculate_gold_value'),


    path('save-pickup-details/', views.save_pickup_details, name='save_pickup_details'),
    path('schedule-store-visit/', views.schedule_store_visit, name='schedule_store_visit'),

    path('view-old-gold-exchange/<int:user_id>/', views.view_old_gold_exchange, name='view_old_gold_exchange'),
    path('update-pickup-details/<int:pickup_id>/', views.update_pickup_details, name='update_pickup_details'),
    path('update-or-cancel-store-visit/<int:store_visit_id>/', views.update_or_cancel_store_visit, name='update_or_cancel_store_visit'),

    path('staff/update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('staff/mark-delivery-complete/<int:order_id>/', views.mark_delivery_complete, name='mark_delivery_complete'),

    path('staff/handle-try-at-home/<int:booking_id>/', views.handle_try_at_home_request, name='handle_try_at_home'),



    path('adminhome/add-vendor/', views.add_vendor, name='add_vendor'),
    # path('adminhome/verify-vendor/', views.verify_vendor, name='verify_vendor'),
    # path('adminhome/purchases/', views.view_purchases, name='view_purchases'),


    path('verify-document/', views.verify_document_page, name='verify_document'),
    path('verify-document/analyze/', views.verify_document, name='verify_document_analyze'),

    # Vendor URLs
    path('vendorhome/', views.vendor_home, name='vendor_home'),
    path('vendor/add-product/', views.vendor_add_product, name='vendor_add_product'),
    path('vendor/view-products/', views.vendor_view_products, name='vendor_view_products'),
    path('vendor/edit-product/<int:product_id>/', views.vendor_edit_product, name='vendor_edit_product'),
    path('vendor/delete-product/<int:product_id>/', views.vendor_delete_product, name='vendor_delete_product'),
    path('vendor/pending-orders/', views.vendor_pending_orders, name='vendor_pending_orders'),
    path('vendor/order-history/', views.vendor_order_history, name='vendor_order_history'),
    path('vendor/restock-request/<int:request_id>/', views.handle_restock_request, name='handle_restock_request'),
    path('vendor/restock-requests/', views.vendor_restock_requests, name='vendor_restock_requests'),
    path('vendor/declined-orders/', views.vendor_declined_orders, name='vendor_declined_orders'),
    path('vendor/payment-details/', views.vendor_payment_details, name='vendor_payment_details'),
    path('vendor/products/<int:product_id>/toggle-status/', views.vendor_toggle_product_status, name='vendor_toggle_product_status'),
    path('vendor/products/<int:product_id>/restock/', views.vendor_restock_product, name='vendor_restock_product'),
    path('vendor/products/<int:product_id>/cancel/', views.vendor_cancel_order, name='vendor_cancel_order'),

    path('update_payment_status/<int:payment_id>/', views.update_payment_status, name='update_payment_status'),
    path('process_payment/', views.process_payment, name='process_payment'),

    path('view_new_products/', views.view_new_products, name='view_new_products'),
    path('send_purchase_request/', views.send_purchase_request, name='send_purchase_request'),

    path('search-by-image/', views.search_by_image, name='search_by_image'),

   


    path('jewelry_assistant/', views.jwellery_view, name='jewelry_assistant'),
    path('get_response/', views.get_response, name='get_response'),
    path('validate_image/', views.validate_image, name='validate_image'),
    path('validate_query/', views.validate_query, name='validate_query'),

    path('view_all_orders/', views.view_all_orders, name='view_all_orders'),

    path('view_payments/', views.view_payments, name='view_payments'),  # New URL for viewing payments






    
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






    #     path('supplier_home/', views.supplier_home, name='supplier_home'),
    # path('supplier/add-product/', views.add_supplier_product, name='add_supplier_product'),
    # path('supplier/view-products/', views.view_supplier_products, name='view_supplier_products'),