import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from graphene_django.filter import DjangoFilterConnectionField
from decimal import Decimal
from django.utils import timezone

# from .mutations import CreateCustomer, BulkCreateCustomers
# from crm.models import Customer, Product, Order


# ? Types
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
    def mutate(cls, root, info, input):
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
            customer = Customer.objects.create(
                name=input.name, email=input.email, phone=input.phone
            )
            customer.save()
        except Exception as exc:
            errors.append(f"Failed to create customer: {str(exc)}")
            return CreateCustomer(customer=None, message="", errors=errors)

        return CreateCustomer(
            customer=customer, message="Customer created successfully.", errors=None
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

        # ? Validate data
        for index, data in enumerate(inputs):
            row = index + 1
            if not data.email:
                errors.append(f"Row {row}: Email is required.")
                continue

            # ? Validate email format
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

            # ? Validate phone if provided
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

        # ? Create valid entries
        try:
            with transaction.atomic():
                for data in valid_entries:
                    c = Customer.objects.create(
                        name=data.name, email=data.email, phone=data.phone
                    )
                    created.append(c)
        except IntegrityError as exc:
            errors.append(f"Database error: {str(exc)}")
        Customer.save()
        return BulkCreateCustomers(customers=created, errors=errors or None)


# Create product
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        errors = []

        try:
            price = Decimal(str(input.price))
        except Exception:
            errors.append("Price must be a valid number.")
            return CreateProduct(product=None, errors=errors)

        if price <= 0:
            errors.append("Price must be positive.")
        stock = input.stock if input.stock is not None else 0
        if stock < 0:
            errors.append("Stock cannot be negative.")

        if errors:
            return CreateProduct(product=None, errors=errors)

        try:
            product = Product.objects.create(name=input.name, price=price, stock=stock)
        except Exception as exc:
            errors.append(f"Failed to create product: {str(exc)}")
            return CreateProduct(product=None, errors=errors)

        return CreateProduct(product=product, errors=None)


# Create order
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        errors = []

        # Validate customer
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            errors.append("Invalid customer ID.")
            return CreateOrder(order=None, errors=errors)

        # Validate products
        if not input.product_ids or len(input.product_ids) == 0:
            errors.append("At least one product must be provided.")
            return CreateOrder(order=None, errors=errors)

        products = []
        for pid in input.product_ids:
            try:
                p = Product.objects.get(pk=pid)
                products.append(p)
            except Product.DoesNotExist:
                errors.append(f"Invalid product ID: {pid}")

        if errors:
            return CreateOrder(order=None, errors=errors)

        total = sum((p.price for p in products), Decimal("0.00"))
        order_dt = input.order_date if input.order_date else timezone.now()

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer, total_amount=total, order_date=order_dt
                )
                order.products.set(products)
                order.save()
        except Exception as exc:
            errors.append(f"Failed to create order: {str(exc)}")
            return CreateOrder(order=None, errors=errors)

        return CreateOrder(order=order, errors=None)


# ? MUTATIONS
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    create_order = CreateOrder.Field()


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
