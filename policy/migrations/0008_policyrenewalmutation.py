# Generated by Django 3.2.19 on 2023-08-30 16:33

import core.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_alter_jsonext_column_in_tblOfficer'),
        ('policy', '0007_fix_policy_mutation_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PolicyRenewalMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='policy_renewals', to='core.mutationlog')),
                ('policy_renewal', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='policy.policyrenewal')),
            ],
            options={
                'db_table': 'policy_renewal_PolicyMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
    ]