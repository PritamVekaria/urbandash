from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/provider/', views.provider_dashboard, name='provider_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('services/add/', views.add_service, name='add_service'),
    path('book/<int:service_id>/', views.book_service, name='book_service'),
    path('payment/<int:booking_id>/', views.make_payment, name='make_payment'),
    path('receipt/pdf/<int:payment_id>/', views.download_receipt_pdf, name='download_receipt_pdf'),
    path('admin/export/bookings/', views.export_bookings_csv, name='export_bookings_csv'),
    path('admin/export/payments/', views.export_payments_csv, name='export_payments_csv'),
    path('admin/export/pdf/', views.generate_admin_report_pdf, name='admin_report_pdf'),


]
