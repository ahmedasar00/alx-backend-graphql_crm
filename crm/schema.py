import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation
from graphene import Mutation
from .mutations import (
    CreateCustomer,
    BulkCreateCustomers,
    CreateProduct,
    CreateOrder,
)


class Query(CRMQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
