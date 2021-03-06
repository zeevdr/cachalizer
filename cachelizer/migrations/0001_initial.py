# Generated by Django 3.1.4 on 2020-12-08 15:41

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, validators=[django.core.validators.MinLengthValidator(2, message='name must be at least 2 characters long')])),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True, validators=[django.core.validators.MinLengthValidator(2, message='name must be at least 2 characters long')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(db_index=True, max_length=100, validators=[django.core.validators.MinLengthValidator(2, message='name must be at least 2 characters long')])),
                ('last_name', models.CharField(db_index=True, max_length=100, validators=[django.core.validators.MinLengthValidator(2, message='name must be at least 2 characters long')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(db_index=True, related_name='people', to='cachelizer.Group')),
                ('pet', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owners', to='cachelizer.dog')),
            ],
        ),
    ]
