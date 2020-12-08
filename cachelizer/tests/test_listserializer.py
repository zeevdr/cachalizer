from django.test import TestCase

from cachelizer.models import Person, Dog
from .__serializers4testing import DogModelWithRandSerializer, PersonModelWithRandSerializer


# Create your tests here.


class ListSerializerTestCase(TestCase):

    def setUp(self):
        PersonModelWithRandSerializer.get_cache().clear()
        DogModelWithRandSerializer.get_cache().clear()
        self.dog_1: Dog = Dog.objects.create(name="Rexy")
        self.person_1 = Person.objects.create(first_name="John", last_name="Doa", pet=self.dog_1)
        self.person_2 = Person.objects.create(first_name="David", last_name="Dodo", pet=self.dog_1)


    def test_list_serializer_scope(self):
        data_people_1 = PersonModelWithRandSerializer([self.person_1], many=True).data
        person_data_1 = PersonModelWithRandSerializer(self.person_1).data
        self.assertEqual(data_people_1[0]["rand"], person_data_1["rand"])

        PersonModelWithRandSerializer.get_cache().clear()

        data_people_2 = PersonModelWithRandSerializer([self.person_1], cache_scope=True, many=True).data
        person_data_2 = PersonModelWithRandSerializer(self.person_1).data
        self.assertNotEqual(data_people_2[0]["rand"], person_data_2["rand"])

    def test_nested_list_serializer_scope(self):

        with DogModelWithRandSerializer.cache_scope():
            person1_data3, person2_data3 = PersonModelWithRandSerializer([self.person_1, self.person_2], many=True).data

        self.assertEqual(person1_data3["pet"]["rand"], person2_data3["pet"]["rand"])

        dog_1_data_3 = DogModelWithRandSerializer(self.dog_1).data

        self.assertNotEqual(person1_data3["pet"]["rand"], dog_1_data_3["rand"])
