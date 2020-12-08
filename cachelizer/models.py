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

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="people", db_index=True,)

    created_at = models.DateTimeField(null=False, blank=False, editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, blank=False, editable=False, auto_now=True)
