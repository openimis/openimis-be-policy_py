# Generated by Django 4.2.11 on 2024-06-04 11:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('insuree', '0030_remove_familymutation_family_uuid_and_more'),
        ('policy', '0010_remove_policy_family_uuid_alter_policy_family'),
    ]

    operations = [
        migrations.AlterField(
            model_name='policy',
            name='family',
            field=models.ForeignKey(blank=True, db_column='FamilyID', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='policies', to='insuree.family'),
        ),
    ]
