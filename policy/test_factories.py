import datetime

import factory

from policy.models import Policy


def _current_year_start():
    return datetime.date(datetime.date.today().year, 1, 1)


def _current_year_end():
    return datetime.date(datetime.date.today().year, 12, 31)


class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    status = Policy.STATUS_ACTIVE
    stage = Policy.STAGE_NEW
    enroll_date = factory.LazyFunction(_current_year_start)
    start_date = factory.LazyFunction(_current_year_start)
    validity_from = factory.LazyFunction(_current_year_start)
    effective_date = factory.LazyFunction(_current_year_start)
    expiry_date = factory.LazyFunction(_current_year_end)
    audit_user_id = -1
