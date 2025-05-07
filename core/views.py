from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import RegistrationForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import Service
from .forms import ServiceForm
from .models import Payment
from .forms import PaymentForm
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Booking
from .forms import BookingForm
from django.contrib.auth.decorators import user_passes_test
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.utils.timezone import now, timedelta
from django.db.models import Count, Sum
from .decorators import customer_required, provider_required, admin_required
import csv


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Login successful! Welcome, {user.username}.")
            
            # Redirect based on role
            if user.role == 'customer':
                return redirect('customer_dashboard')
            elif user.role == 'provider':
                return redirect('provider_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# Check if user is a service provider
def provider_check(user):
    return user.is_authenticated and user.role == 'provider'

@user_passes_test(provider_check)
def provider_dashboard(request):
    services = Service.objects.filter(provider=request.user)
    return render(request, 'dashboards/provider_dashboard.html', {
        'user': request.user,
        'services': services
    })

@user_passes_test(provider_check)
def add_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = request.user
            service.save()
            return redirect('provider_dashboard')
    else:
        form = ServiceForm()
    return render(request, 'services/add_service.html', {'form': form})

@login_required
def customer_dashboard(request):
    query = request.GET.get('q', '')
    services = Service.objects.all()

    if query:
        services = services.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    return render(request, 'dashboards/customer_dashboard.html', {
        'user': request.user,
        'services': services,
        'query': query,
    })

@login_required
def book_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if request.user.role != 'customer':
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.service = service
            booking.status = 'pending'
            booking.save()
            return render(request, 'booking/confirmation.html', {'booking': booking})
    else:
        form = BookingForm()

    return render(request, 'booking/book_service.html', {
        'form': form,
        'service': service
    })

@login_required
def make_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

    if hasattr(booking, 'payment'):
        return render(request, 'payment/already_paid.html', {'booking': booking})

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.amount = 100.00
            payment.status = 'paid'
            payment.save()
            booking.status = 'confirmed'
            booking.save()
            return render(request, 'payment/payment_success.html', {'payment': payment})
    else:
        form = PaymentForm()

    return render(request, 'payment/make_payment.html', {
        'form': form,
        'booking': booking
    })

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response

@admin_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('login')

    today = now().date()
    this_week = today - timedelta(days=7)
    this_month = today - timedelta(days=30)

    total_users = CustomUser.objects.count()
    total_services = Service.objects.count()
    total_bookings = Booking.objects.count()
    total_payments = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    daily_bookings = Booking.objects.filter(created_at__date=today).count()
    weekly_bookings = Booking.objects.filter(created_at__date__gte=this_week).count()
    monthly_bookings = Booking.objects.filter(created_at__date__gte=this_month).count()

    recent_bookings = Booking.objects.select_related('service', 'customer').order_by('-created_at')[:10]
    recent_payments = Payment.objects.select_related('booking').order_by('-paid_at')[:10]

    return render(request, 'admin/admin_dashboard.html', {
        'total_users': total_users,
        'total_services': total_services,
        'total_bookings': total_bookings,
        'total_payments': total_payments,
        'daily_bookings': daily_bookings,
        'weekly_bookings': weekly_bookings,
        'monthly_bookings': monthly_bookings,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
    })

@admin_required
def export_bookings_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Booking ID', 'Customer', 'Service', 'Date', 'Time', 'Status'])

    bookings = Booking.objects.select_related('customer', 'service').all()
    for b in bookings:
        writer.writerow([b.id, b.customer.username, b.service.title, b.date, b.time, b.status])

    return response

@admin_required
def export_payments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Payment ID', 'Booking ID', 'Customer', 'Amount', 'Transaction Code', 'Date'])

    payments = Payment.objects.select_related('booking', 'booking__customer').all()
    for p in payments:
        writer.writerow([
            p.id,
            p.booking.id,
            p.booking.customer.username,
            p.amount,
            p.transaction_code,
            p.paid_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response

def generate_admin_report_pdf(request):
    if request.user.role != 'admin':
        return redirect('login')

    data = {
        'total_users': CustomUser.objects.count(),
        'total_services': Service.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_payments': Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'recent_bookings': Booking.objects.order_by('-created_at')[:5],
        'recent_payments': Payment.objects.order_by('-paid_at')[:5],
    }
    return render_to_pdf('admin/report_pdf.html', data)


@login_required
def download_receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, booking__customer=request.user)
    return render_to_pdf('payment/receipt_pdf.html', {'payment': payment})

@customer_required
def customer_dashboard(request):
    return render(request, 'dashboards/customer_dashboard.html', {'user': request.user})

@provider_required
def provider_dashboard(request):
    return render(request, 'dashboards/provider_dashboard.html', {'user': request.user})

@login_required
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html', {'user': request.user})
