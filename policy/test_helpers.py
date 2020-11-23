from insuree.models import InsureePolicy
from policy.models import Policy


def create_test_policy(product, insuree, link=True, valid=True, custom_props=None):
    """
    Compatibility method that only return the Policy
    """
    return create_test_policy2(product, insuree, link, valid, custom_props)[0]


def create_test_policy2(product, insuree, link=True, valid=True, custom_props=None):
    """
    Creates a Policy and optionally an InsureePolicy
    :param product: Product on which this Policy is based
    :param insuree: The Policy will be linked to this Insuree's family and if link is True, the InsureePolicy will
     belong to him
    :param link: if True (default), an InsureePolicy will also be created
    :param valid: Whether the created Policy should be valid (validity_to)
    :param custom_props: dictionary of custom values for the Policy, when overriding a foreign key, override the _id
    :return: The created Policy and InsureePolicy
    """
    policy = Policy.objects.create(
        **{
            "family": insuree.family,
            "product": product,
            "status": Policy.STATUS_ACTIVE,
            "stage": Policy.STAGE_NEW,
            "enroll_date": "2019-01-01",
            "start_date": "2019-01-02",
            "validity_from": "2019-01-01",
            "effective_date": "2019-01-01",
            "expiry_date": "2039-06-01",
            "validity_to": None if valid else "2019-01-01",
            "audit_user_id": -1,
            **(custom_props if custom_props else {})
        }
    )
    if link:
        insuree_policy = InsureePolicy.objects.create(
            insuree=insuree,
            policy=policy,
            audit_user_id=-1,
            effective_date="2019-01-01",
            expiry_date="2039-06-01",
            validity_from="2019-01-01",
            validity_to=None if valid else "2019-01-01",
        )
    else:
        insuree_policy = None
    return policy, insuree_policy
