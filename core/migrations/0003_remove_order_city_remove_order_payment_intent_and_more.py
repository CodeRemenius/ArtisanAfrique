# Generated by Django 5.0.4 on 2024-04-30 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_userprofile_is_customer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='city',
        ),
        migrations.RemoveField(
            model_name='order',
            name='payment_intent',
        ),
        migrations.RemoveField(
            model_name='order',
            name='zipcode',
        ),
    ]
