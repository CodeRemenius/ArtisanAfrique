# Generated by Django 5.0.4 on 2024-05-07 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_haggle'),
    ]

    operations = [
        migrations.AddField(
            model_name='haggle',
            name='is_rejected',
            field=models.BooleanField(default=False),
        ),
    ]
