# Generated by Django 5.2 on 2025-04-30 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0008_alter_transactionconfig_get_balance_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionconfig',
            name='get_balance_url',
            field=models.URLField(default=''),
        ),
        migrations.AlterField(
            model_name='transactionconfig',
            name='statement_url',
            field=models.URLField(blank=True, default='', null=True),
        ),
    ]
