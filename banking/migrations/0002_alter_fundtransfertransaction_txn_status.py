# Generated by Django 5.2 on 2025-04-27 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fundtransfertransaction',
            name='txn_status',
            field=models.CharField(choices=[('INITIATED', 'Initiated'), ('ACPT', 'Accepted'), ('REJECTED', 'Rejected'), ('FAILED', 'Failed'), ('ERROR', 'Error')], default='INITIATED', max_length=20),
        ),
    ]
