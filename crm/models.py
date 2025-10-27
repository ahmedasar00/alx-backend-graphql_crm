from django.db import models
from django.core.validators import EmailValidator, MinValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal


# Create your models here.
phone_validator = RegexValidator(
    regex=r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$",
    message="Phone must be like +1234567890 or 123-456-7890",
)


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone = models.CharField(
        max_length=30, blank=True, null=True, validators=[phone_validator]
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal(0.01))]
    )
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    products = models.ManyToManyField(Product, related_name="orders")
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal(0.00)
    )

    def __str__(self):
        return f"Order {self.id} - {self.customer.name} - {self.total_amount}"
