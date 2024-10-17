from contribution.models import Premium
from insuree.models import InsureePolicy
from insuree.test_helpers import create_test_insuree
from policy.models import Policy
from policy.values import policy_values
from product.models import Product
from core.utils import filter_validity
from core.test_helpers import create_test_interactive_user
import datetime


def create_test_policy(
    product, insuree, link=True, valid=True, custom_props=None, check=False
):
    """
    Compatibility method that only return the Policy
    """
    return create_test_policy2(product, insuree, link, valid, custom_props, check)[0]


def dts(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def create_test_policy2(
    product, insuree, link=True, valid=True, custom_props=None, check=False
):
    user = create_test_interactive_user()
    """
    Creates a Policy and optionally an InsureePolicy
    :param product: Product on which this Policy is based (or its ID)
    :param insuree: The Policy will be linked to this Insuree's family and if link is True, the InsureePolicy will
     belong to him
    :param link: if True (default), an InsureePolicy will also be created
    :param valid: Whether the created Policy should be valid (validity_to)
    :param custom_props: dictionary of custom values for the Policy, when overriding a foreign key, override the _id
    :return: The created Policy and InsureePolicy
    """
    policy_qs = Policy.objects.filter(
        family=insuree.family, product=product, *filter_validity()
    )
    if custom_props is None:
        custom_props = {}
    else:
        custom_props = {k: v for k, v in custom_props.items() if hasattr(Policy, k)}
    if custom_props:
        policy_qs = policy_qs.filter(**custom_props)
    policy = policy_qs.first()

    fallback_start_date = datetime.date(datetime.date.today().year, 1, 1)
    fallback_end_date = datetime.date(datetime.date.today().year, 12, 31)

    if not policy:
        policy = Policy.objects.create(
            **{
                "family": insuree.family,
                "product_id": product.id if isinstance(product, Product) else product,
                "status": Policy.STATUS_ACTIVE,
                "stage": Policy.STAGE_NEW,
                "enroll_date": fallback_start_date,
                "start_date": fallback_start_date,
                "validity_from": fallback_start_date,
                "effective_date": fallback_start_date,
                "expiry_date": fallback_end_date,
                "validity_to": None if valid else fallback_start_date,
                "audit_user_id": -1,
                **custom_props,
            }
        )
    elif custom_props:
        policy.update(**custom_props)

    if link:
        insuree_policy = InsureePolicy.objects.filter(
            insuree=insuree, policy=policy, *filter_validity()
        ).first()
        if not insuree_policy:
            insuree_policy = InsureePolicy.objects.create(
                insuree=insuree,
                policy=policy,
                audit_user_id=-1,
                effective_date=policy.effective_date,
                expiry_date=policy.expiry_date,
                validity_from=policy.validity_from,
                validity_to=None if valid else policy.validity_from,
            )
    else:
        insuree_policy = None
    # Was added for OMT-333 but breaks tests that explicitly call policy_values
    policy, warnings = policy_values(
        policy, insuree.family, None, user, members=[insuree]
    )
    if check and warnings:
        raise Exception("Policy has warnings: {}".format(warnings))

    return policy, insuree_policy


def create_test_policy_with_IPs(
    product, insuree, valid=True, policy_props=None, IP_props=None, premium_props=None
):
    """
    Creates a Policy with its related InsureePolicys for each Family member.
    :param product: Product on which this Policy is based (or its ID)
    :param insuree: The Policy will be linked to this Insuree's family
    :param valid: Whether the created Policy should be valid (validity_to)
    :param policy_props: dictionary of custom values for the Policy, when overriding a foreign key, override the _id
    :param IP_props: dictionary of custom values for the InsureePolicy, when overriding a foreign key, override the _id
    :param premium_props: dictionary of custom values for the Premium, when overriding a foreign key, override the _id
    :return: The created Policy and InsureePolicy
    """
    value = 10000.00
    default_date = dts("2019-01-01")
    start_date = dts("2019-01-02")
    expiry_date = dts("2039-06-01")

    policy = Policy.objects.create(
        **{
            "family": insuree.family,
            "product_id": product.id if isinstance(product, Product) else product,
            "status": Policy.STATUS_ACTIVE,
            "stage": Policy.STAGE_NEW,
            "enroll_date": default_date,
            "start_date": start_date,
            "validity_from": default_date,
            "effective_date": default_date,
            "expiry_date": expiry_date,
            "value": value,
            "validity_to": None if valid else default_date,
            "audit_user_id": -1,
            **(policy_props if policy_props else {}),
        }
    )

    for member in policy.family.members.filter(validity_to__isnull=True):
        InsureePolicy.objects.create(
            **{
                "insuree": member,
                "policy": policy,
                "audit_user_id": -1,
                "effective_date": default_date,
                "expiry_date": expiry_date,
                "start_date": start_date,
                "enrollment_date": default_date,
                "validity_from": default_date,
                "validity_to": None if valid else default_date,
                **(IP_props if IP_props else {}),
            }
        )

    Premium.objects.create(
        **{
            "amount": value,
            "receipt": "TEST1234",
            "pay_date": default_date,
            "pay_type": "C",
            "validity_from": default_date,
            "policy_id": policy.id,
            "audit_user_id": -1,
            "validity_to": None if valid else default_date,
            "created_date": default_date,
            **(premium_props if premium_props else {}),
        }
    )
    # reseting custom props to avoid having it in next calls
    policy_props = {}
    IP_props = {}
    premium_props = {}
    return policy


def create_test_insuree_for_policy(
    with_family=True, is_head=False, custom_props=None, family_custom_props=None
):
    # To establish the mandatory reference between "Insuree" and "Family" objects, we can insert the "Family" object
    # with a temporary ID and later update it to associate with the respective "Insuree" object.
    insuree = create_test_insuree(
        with_family=with_family,
        is_head=is_head,
        custom_props=custom_props,
        family_custom_props=family_custom_props,
    )

    family_custom_props = {}

    return insuree, insuree.family
