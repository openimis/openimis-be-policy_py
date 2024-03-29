# Generated by Django 3.2.18 on 2023-05-12 08:48

import core.fields
import datetime
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0013_auto_20211103_1023'),
        ('core', '0019_extended_field'),
        ('product', '0006_insert_ceiling_type'),
        ('policy', '0004_add_medical_oficer_reading_rights'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='policy',
            name='row_id',
        ),
        migrations.AddField(
            model_name='policy',
            name='family',
            field=models.ForeignKey(db_column='FamilyID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='policies', to='insuree.family'),
        ),
        migrations.AddField(
            model_name='policy',
            name='officer',
            field=models.ForeignKey(blank=True, db_column='OfficerID', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='policies', to='core.officer'),
        ),
        migrations.AddField(
            model_name='policy',
            name='product',
            field=models.ForeignKey(db_column='ProdID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='policies', to='product.product'),
        ),
        migrations.AddField(
            model_name='policy',
            name='uuid',
            field=models.CharField(db_column='PolicyUUID', default=uuid.uuid4, max_length=36, unique=True),
        ),
        migrations.AddField(
            model_name='policyrenewal',
            name='insuree',
            field=models.ForeignKey(db_column='InsureeID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='policy_renewals', to='insuree.insuree'),
        ),
        migrations.AddField(
            model_name='policyrenewal',
            name='new_officer',
            field=models.ForeignKey(blank=True, db_column='NewOfficerID', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='policy_renewals', to='core.officer'),
        ),
        migrations.AddField(
            model_name='policyrenewal',
            name='new_product',
            field=models.ForeignKey(db_column='NewProdID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='policy_renewals', to='product.product'),
        ),
        migrations.AddField(
            model_name='policyrenewal',
            name='policy',
            field=models.ForeignKey(db_column='PolicyID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='policy_renewals', to='policy.policy'),
        ),
        migrations.AlterField(
            model_name='policy',
            name='validity_from',
            field=core.fields.DateTimeField(db_column='ValidityFrom', default=datetime.datetime.now),
        ),
    ]
