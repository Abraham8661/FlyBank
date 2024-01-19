# Generated by Django 5.0 on 2024-01-10 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_account_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='account_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='phone_number',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
