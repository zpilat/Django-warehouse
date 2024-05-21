import graphene
from graphene_django.types import DjangoObjectType
from .models import Sklad

class SkladType(DjangoObjectType):
    class Meta:
        model = Sklad

class Query(graphene.ObjectType):
    all_sklad = graphene.List(SkladType)

    def resolve_all_sklad(self, info, **kwargs):
        return Sklad.objects.all()

schema = graphene.Schema(query=Query)
