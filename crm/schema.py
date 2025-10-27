import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError


# ? Types

from crm.models import Customer, Product, Order


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


# ? Inputs
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=True)


class OrderInput(graphene.InputObjectType):
    Customer_id = graphene.ID(required=True)
    Product_id = graphene.List(graphene.ID, required=True)
    order_date = graphene.types.datetime.DateTime(required=False)


##? Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    @classmethod
    def muutate(cls, root, info, input):
        errors = []

        try:
            validate_email(input.email)
        except DjangoValidationError:
            errors.append("Invalid email format.")
            return CreateCustomer(customer=None, message="", errors=errors)
        if input.phone:
            phone_validator = RegexValidator(
                regex=r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$",
                message="Phone must be like +1234567890 or 123-456-7890",
            )
            try:
                phone_validator(input.phone)
            except DjangoValidationError:
                errors.append(
                    "Invalid phone number format. Use +1387986981 or 432-234-3232."
                )
                return CreateCustomer(customer=None, message="", errors=errors)
        if Customer.objects.filter(email=input.email).exists():
            errors.append("Email already exists.")
            return CreateCustomer(customer=None, message="", errors=errors)

        try:
            Customer = Customer.objects.craate(
                name=input.name, email=input.email, phone=input.phone
            )
        except Exception as exc:
            errors.append(f"Failed to create customer: {str(exc)}")
            return CreateCustomer(customer=None, message="", errors=errors)

        return CreateCustomer(
            customer=Customer, message="Customer created successfully.", errors=None
        )


# Bulk create customers
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)

    customer = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, inputs):
        created = []
        errors = []
        seen_emails = set()
        valid_entries = []

        for index, data in enumerate(inputs):
            row = index + 1
            if not data.email:
                errors.append(f"Row {row}: Email is required.")
                continue

            try:
                validate_email(data.email)
            except DjangoValidationError:
                errors.append(f"Row {row}: invalid email format ({data.email}).")
                continue

            if (
                data.email in seen_emails
                or Customer.objects.filter(email=data.email).exists()
            ):
                errors.append(f"Row {row}: Email already exists ({data.email}).")
                continue

            if data.phone:
                phone_validator = RegexValidator(
                    regex=r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$",
                    message="Phone must be like +1234567890 or 123-456-7890",
                )

                try:
                    phone_validator(data.phone)
                except DjangoValidationError:
                    errors.append(
                        f"Row {row}: Invalid phone number format ({data.phone})."
                    )
                    continue

            seen_emails.add(data.email)
            valid_entries.append(data)

        # Create valid entries
        try:
            with transaction.atomic():
                for data in valid_entries:
                    c = Customer.objects.create(
                        name=data.name, email=data.email, phone=data.phone
                    )
                    created.append(c)
        except IntegrityError as exc:
            errors.append(f"Database error: {str(exc)}")

        return BulkCreateCustomers(customers=created, errors=errors or None)


# ?  QUERIES
class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()

    def resolve_all_products(root, info):
        return Product.objects.all()

    def resolve_all_orders(root, info):
        return Order.objects.all()
