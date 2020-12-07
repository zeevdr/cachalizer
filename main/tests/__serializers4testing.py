from rest_framework import serializers

from main.cache_serializer import CashedSerializerMeta
from main.models import Person, Group


class PersonModelSerializer(serializers.ModelSerializer, metaclass=CashedSerializerMeta):

    class Meta:
        model = Person
        fields = ("id", "first_name", "last_name",)

    def to_representation(self, instance):
        return super().to_representation(instance)


class GroupModelSerializer(serializers.ModelSerializer, metaclass=CashedSerializerMeta):
    people = PersonModelSerializer(many=True)

    class Meta:
        model = Group
        fields = ("id", "name", "people",)
