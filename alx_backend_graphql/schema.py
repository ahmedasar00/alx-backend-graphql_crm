import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String(description="Hello field")

    def resolve_hello(self, info):
        return "Hello, GraphQL! Ahmed 3sar"


schema = graphene.Schema(query=Query, mutation=CRMMutation)
