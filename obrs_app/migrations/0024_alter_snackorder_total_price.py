# Generated by Django 5.1.4 on 2025-03-22 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obrs_app', '0023_snackorder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='snackorder',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
