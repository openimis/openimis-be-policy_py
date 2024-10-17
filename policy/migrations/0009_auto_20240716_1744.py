# Generated by Django 3.2.19 on 2024-07-16 17:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("policy", "0008_remove_policy_row_id_policy_contribution_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="policy",
            name="creation_date",
            field=models.DateField(
                blank=True,
                default=django.utils.timezone.now,
                db_column="creationDate",
                null=True,
            ),
        ),
    ]
