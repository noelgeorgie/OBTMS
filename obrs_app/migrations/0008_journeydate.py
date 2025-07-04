# Generated by Django 5.1.4 on 2025-02-08 15:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obrs_app', '0007_attendance_schedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='JourneyDate',
            fields=[
                ('journey_id', models.AutoField(primary_key=True, serialize=False)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='obrs_app.schedule')),
            ],
        ),
    ]
