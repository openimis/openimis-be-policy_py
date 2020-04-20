from insuree.models import InsureePolicy
from policy.models import Policy


def create_test_policy(product, insuree, link=True, valid=True, custom_props=None):
    policy = Policy.objects.create(
        **{
            "family": insuree.family,
            "product": product,
            "status": Policy.STATUS_ACTIVE,
            "stage": Policy.STAGE_NEW,
            "enroll_date": "2019-06-01",
            "start_date": "2019-06-02",
            "validity_from": "2019-06-01",
            "effective_date": "2019-06-01",
            "expiry_date": "2039-06-01",
            "validity_to": None if valid else "2019-06-01",
            "audit_user_id": -1,
            **(custom_props if custom_props else {})
        }
    )
    if link:
        insuree_policy = InsureePolicy.objects.create(
            insuree=insuree,
            policy=policy,
            audit_user_id=-1,
            effective_date="2019-06-01",
            expiry_date="2039-06-01",
            validity_from="2019-06-01",
            validity_to=None if valid else "2019-06-01",
        )
    return policy
