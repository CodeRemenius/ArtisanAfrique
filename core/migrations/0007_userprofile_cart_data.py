# Generated by Django 5.0.4 on 2024-05-06 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_order_is_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cart_data',
            field=models.TextField(default='{}'),
        ),
    ]
