import graphene


class Query(graphene.ObjectType):
    hello = graphene.String(description="Hello, GraphQL! Ahmed 3sar")


schema = graphene.Schema(query=Query)
