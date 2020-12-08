from django.db import models
from django.core import validators


class Group(models.Model):
    name = models.CharField(null=False, blank=False, db_index=True, unique=True,
                            max_length=100,
                            validators=(validators.MinLengthValidator(
                                2, message="name must be at least 2 characters long"),), )

    created_at = models.DateTimeField(null=False, blank=False, editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, blank=False, editable=False, auto_now=True)


class Person(models.Model):
    first_name = models.CharField(null=False, blank=False, db_index=True,
                                  max_length=100,
                                  validators=(validators.MinLengthValidator(
                                      2, message="name must be at least 2 characters long"),), )

    last_name = models.CharField(null=False, blank=False, db_index=True,
                                 max_length=100,
                                 validators=(validators.MinLengthValidator(
                                     2, message="name must be at least 2 characters long"),), )

    groups = models.ManyToManyField(Group, related_name="people", db_index=True, )

    created_at = models.DateTimeField(null=False, blank=False, editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, blank=False, editable=False, auto_now=True)

    pet = models.ForeignKey("Dog", null=True, blank=True, default=None, related_name="owners", on_delete=models.SET_NULL)


class Dog(models.Model):
    name = models.CharField(null=False, blank=False, db_index=True,
                            max_length=100,
                            validators=(validators.MinLengthValidator(
                                2, message="name must be at least 2 characters long"),), )
