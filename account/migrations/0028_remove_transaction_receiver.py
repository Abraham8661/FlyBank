# Generated by Django 5.0 on 2024-01-11 10:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0027_rename_intended_amount_transaction_amount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='receiver',
        ),
    ]
