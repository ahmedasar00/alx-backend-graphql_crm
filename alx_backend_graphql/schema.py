import graphene

from crm.schema import Query as CRMQuery


class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String(description="Hello, GraphQL! Ahmed 3sar")


schema = graphene.Schema(query=Query)
