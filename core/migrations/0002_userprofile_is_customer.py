# Generated by Django 5.0.4 on 2024-04-29 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_customer',
            field=models.BooleanField(default=False),
        ),
    ]
