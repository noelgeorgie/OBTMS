# Generated by Django 5.1.4 on 2025-05-01 07:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obrs_app', '0035_alter_bus_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='bus_images/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='obrs_app.bus')),
            ],
        ),
    ]
