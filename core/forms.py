from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import Service
from .models import Booking
from .models import Payment

class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'phone', 'address', 'password1', 'password2']

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'description', 'category', 'booking_fee']

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['transaction_code']
        widgets = {
            'transaction_code': forms.TextInput(attrs={'placeholder': 'e.g. MPESA123456'}),
        }