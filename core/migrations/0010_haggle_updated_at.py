# Generated by Django 5.0.4 on 2024-05-25 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_haggle_is_rejected'),
    ]

    operations = [
        migrations.AddField(
            model_name='haggle',
            name='updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]