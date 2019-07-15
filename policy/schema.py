import graphene
from graphene_django import DjangoObjectType
from .models import Policy


class PolicyType(DjangoObjectType):
    class Meta:
        model = Policy
        exclude_fields = ('row_id',)


class Query(graphene.ObjectType):
    all_policies = graphene.List(PolicyType)

    def resolve_all_policies(self, info, **kwargs):
        return Policy.objects.all()
