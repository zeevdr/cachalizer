from django.test import TestCase

# Create your tests here.
from rest_framework import serializers

from main.cache_serializer import cached_serializer
from main.models import Person, Group


@cached_serializer
class PersonModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ("id", "first_name", "last_name",)


@cached_serializer
class GroupModelSerializer(serializers.ModelSerializer):
    people = PersonModelSerializer(many=True)

    class Meta:
        model = Group
        fields = ("id", "name", "people",)


class DecoratorTestCase(TestCase):

    def setUp(self):
        PersonModelSerializer.get_cache().clear()
        self.group_1 = Group.objects.create(name="Some Group")
        self.person_1 = Person.objects.create(first_name="John", last_name="Doa", group=self.group_1)
        self.person_2 = Person.objects.create(first_name="David", last_name="Dodo", group=self.group_1)

    def test_person_serializer(self):
        expected_data1 = {"id": self.person_1.id,
                          "first_name": "John", "last_name": "Doa"}

        sr1 = PersonModelSerializer(self.person_1)
        data1 = sr1.data
        self.assertDictEqual(data1, expected_data1)

        self.person_1.first_name = "john"
        self.person_1.save()

        sr1 = PersonModelSerializer(self.person_1)
        data1 = sr1.data

        self.assertDictEqual(data1, expected_data1)

        sr2 = PersonModelSerializer(self.person_1)
        data2 = sr2.data

        self.assertDictEqual(data2, expected_data1)

        expected_data2 = {"id": self.person_1.id,
                          "first_name": "john", "last_name": "Doa"}

        PersonModelSerializer.invalidate_cache(self.person_1)
        sr1 = PersonModelSerializer(self.person_1)
        data1 = sr1.data

        self.assertDictEqual(data1, expected_data2)
