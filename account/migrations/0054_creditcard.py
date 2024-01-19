# Generated by Django 5.0 on 2024-01-17 11:10

import django.db.models.deletion
import shortuuid.django_fields
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0053_notification_transaction_alter_notification_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('card_balance', models.FloatField(default=0.0)),
                ('card_type', models.CharField(choices=[('visa', 'VISA'), ('master', 'MASTER'), ('verve', 'VERVE')], max_length=100)),
                ('card_name', models.CharField(max_length=500)),
                ('card_number', shortuuid.django_fields.ShortUUIDField(alphabet='1234567890', length=14, max_length=16, prefix='85', unique=True)),
                ('CVV', shortuuid.django_fields.ShortUUIDField(alphabet='1234567890', length=3, max_length=3, prefix='', unique=True)),
                ('issue_date', models.DateTimeField()),
                ('expiry_date', models.DateTimeField()),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='account.account')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
