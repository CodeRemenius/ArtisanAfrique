# Generated by Django 5.0.4 on 2024-04-30 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_completed',
            field=models.BooleanField(default=False),
        ),
    ]
