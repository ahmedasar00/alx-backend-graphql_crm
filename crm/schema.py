import graphene
from graphene_django import DjangoObjectType
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


# Types

from crm.models import Customer, Product, Order


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrdereType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


class Query(CRMQuery, graphene.ObjectType):
    pass


#! Inputs
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


#!  QUERIES
class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()
