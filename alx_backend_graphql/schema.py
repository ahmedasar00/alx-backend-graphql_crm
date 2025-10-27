import graphene

from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(graphene.ObjectType):
    hello = graphene.String(description="Hello, GraphQL! Ahmed 3sar")


schema = graphene.Schema(query=Query)


class Query(CRMQuery, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
