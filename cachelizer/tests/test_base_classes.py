from django.test import TestCase

from cachelizer.cache_serializer import CashedModelSerializer
from cachelizer.models import Person, Group


# Create your tests here.


class PersonModelSerializer(CashedModelSerializer):

    class Meta:
        model = Person
        fields = ("id", "first_name", "last_name",)

    def to_representation(self, instance):
        return super().to_representation(instance)


class GroupModelSerializer(CashedModelSerializer):
    people = PersonModelSerializer(many=True)

    class Meta:
        model = Group
        fields = ("id", "name", "people",)


class BaseClassTestCase(TestCase):

    def setUp(self):
        PersonModelSerializer.get_cache().clear()
        self.group_1: Group = Group.objects.create(name="Some Group")
        self.person_1 = Person.objects.create(first_name="John", last_name="Doa")
        self.person_2 = Person.objects.create(first_name="David", last_name="Dodo")
        self.group_1.people.add(self.person_1, self.person_2)

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

        PersonModelSerializer(self.person_1).invalidate_cache()
        sr1 = PersonModelSerializer(self.person_1)
        data1 = sr1.data

        self.assertDictEqual(data1, expected_data2)
