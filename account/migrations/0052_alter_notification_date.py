# Generated by Django 5.0 on 2024-01-14 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0051_alter_notification_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
