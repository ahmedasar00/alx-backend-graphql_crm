import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
