import logging
from functools import lru_cache

from django.db import migrations
from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


ROLE_RIGHTS_ID = [101201]  # Read policy by insuree and by family
MEDICAL_OFFICER_SYSTEM_ROLE_ID = 16  # Medical officer


def create_role_right(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    for right_id in ROLE_RIGHTS_ID:
        insert_role_right_for_system(MEDICAL_OFFICER_SYSTEM_ROLE_ID, right_id, apps)


class Migration(migrations.Migration):

    dependencies = [("policy", "0003_auto_20201021_0811")]

    operations = [
        migrations.RunPython(create_role_right),
    ]
