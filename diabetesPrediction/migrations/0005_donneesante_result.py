# Generated by Django 5.0.6 on 2025-04-26 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diabetesPrediction', '0004_donneesante_date_prediction'),
    ]

    operations = [
        migrations.AddField(
            model_name='donneesante',
            name='result',
            field=models.CharField(default='Pending', max_length=100),
        ),
    ]
