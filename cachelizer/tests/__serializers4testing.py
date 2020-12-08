import random

from rest_framework import serializers

from cachelizer.cache_serializer import CashedSerializerMeta
from cachelizer.models import Person, Group, Dog

random.seed()


class PersonModelSerializer(serializers.ModelSerializer, metaclass=CashedSerializerMeta):


    class Meta:
        model = Person
        fields = ("id", "first_name", "last_name",)


class GroupModelSerializer(serializers.ModelSerializer, metaclass=CashedSerializerMeta):
    people = PersonModelSerializer(many=True)

    class Meta:
        model = Group
        fields = ("id", "name", "people",)


class DogModelSerializer(serializers.ModelSerializer, metaclass=CashedSerializerMeta):

    class Meta:
        model = Group
        fields = ("id", "name",)


class DogModelWithRandSerializer(DogModelSerializer):
    rand = serializers.SerializerMethodField()

    class Meta(DogModelSerializer.Meta):
        fields = DogModelSerializer.Meta.fields + ("rand",)

    def get_rand(self, instance):
        return str(random.random())


class PersonModelWithRandSerializer(PersonModelSerializer):
    rand = serializers.SerializerMethodField()
    pet = DogModelWithRandSerializer()

    class Meta(PersonModelSerializer.Meta):
        fields = PersonModelSerializer.Meta.fields + ("rand", "pet")

    def get_rand(self, instance):
        return str(random.random())


class GroupModelWithRandSerializer(GroupModelSerializer):
    people = PersonModelWithRandSerializer(many=True, cache_scope=True)
    rand = serializers.SerializerMethodField()

    class Meta(GroupModelSerializer.Meta):
        fields = GroupModelSerializer.Meta.fields + ("rand",)

    def get_rand(self, instance):
        return str(random.random())
