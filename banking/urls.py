# urls.py
from django.urls import path
from .views import ProcessPaymentAPIView

urlpatterns = [
    path('process-payment/', ProcessPaymentAPIView.as_view(), name='process-payment'),
]
