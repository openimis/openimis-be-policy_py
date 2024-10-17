# Generated by Django 2.1.8 on 2019-04-05 08:15

import core.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Policy",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="PolicyID", primary_key=True, serialize=False
                    ),
                ),
                (
                    "legacy_id",
                    models.IntegerField(blank=True, db_column="LegacyID", null=True),
                ),
                (
                    "stage",
                    models.CharField(
                        blank=True, db_column="PolicyStage", max_length=1, null=True
                    ),
                ),
                (
                    "status",
                    models.SmallIntegerField(
                        blank=True, db_column="PolicyStatus", null=True
                    ),
                ),
                (
                    "value",
                    models.DecimalField(
                        blank=True,
                        db_column="PolicyValue",
                        decimal_places=2,
                        max_digits=18,
                        null=True,
                    ),
                ),
                ("enroll_date", core.fields.DateField(db_column="EnrollDate")),
                ("start_date", core.fields.DateField(db_column="StartDate")),
                (
                    "effective_date",
                    core.fields.DateField(
                        blank=True, db_column="EffectiveDate", null=True
                    ),
                ),
                (
                    "expiry_date",
                    core.fields.DateField(
                        blank=True, db_column="ExpiryDate", null=True
                    ),
                ),
                ("validity_from", core.fields.DateTimeField(db_column="ValidityFrom")),
                (
                    "validity_to",
                    core.fields.DateTimeField(
                        blank=True, db_column="ValidityTo", null=True
                    ),
                ),
                (
                    "offline",
                    models.BooleanField(blank=True, db_column="isOffline", null=True),
                ),
                ("audit_user_id", models.IntegerField(db_column="AuditUserID")),
                (
                    "row_id",
                    models.BinaryField(blank=True, db_column="RowID", null=True),
                ),
            ],
            options={
                "db_table": "tblPolicy",
                "managed": False,
            },
        ),
    ]
