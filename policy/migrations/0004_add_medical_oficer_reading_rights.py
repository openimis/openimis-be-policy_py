import logging
from functools import lru_cache

from django.db import migrations
from core.models import RoleRight, Role


logger = logging.getLogger(__name__)


ROLE_RIGHTS_ID = [101201]  # Read policy by insuree and by family
MEDICAL_OFFICER_SYSTEM_ROLE_ID = 16  # Medical officer


@lru_cache(maxsize=1)
def __get_role_owner() -> Role:
    return Role.objects.get(is_system=MEDICAL_OFFICER_SYSTEM_ROLE_ID, validity_to=None)


def __role_already_exists(right_id):
    sc = RoleRight.objects.filter(role__uuid=__get_role_owner().uuid, right_id=right_id)
    return sc.count() > 0


def create_role_right(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    for right_id in ROLE_RIGHTS_ID:
        if __role_already_exists(right_id):
            logger.warning(F"Role right {right_id} already assigned for role {__get_role_owner().name}, skipping")
            return
        role_owner = Role.objects.get(is_system=MEDICAL_OFFICER_SYSTEM_ROLE_ID, validity_to=None)
        new_role = RoleRight(
            role=role_owner,
            right_id=right_id,
            audit_user_id=None,
        )
        new_role.save()


class Migration(migrations.Migration):

    dependencies = [
        ('policy', '0003_auto_20201021_0811')
    ]

    operations = [
        migrations.RunPython(create_role_right),
    ]
