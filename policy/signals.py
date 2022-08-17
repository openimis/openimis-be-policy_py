from calculation.services import run_calculation_rules
from core.models import User
from core.service_signals import ServiceSignalBindType
from core.signals import Signal, bind_service_signal
from policy.models import Policy

_check_formal_sector_for_policy_signal_params = ["user", "policy_id"]
signal_check_formal_sector_for_policy = Signal(providing_args=_check_formal_sector_for_policy_signal_params)


def bind_service_signals():
    bind_service_signal(
        'policy_service.create_or_update',
        on_policy_create_or_update,
        bind_type=ServiceSignalBindType.AFTER
    )


def on_policy_create_or_update(**kwargs):
    policy = kwargs.get('result', None)
    if policy:
        if policy.status in [Policy.STATUS_IDLE, Policy.STATUS_ACTIVE]:
            user = User.objects.filter(i_user__id=policy.audit_user_id).first()
            # run calcrule for Invoice if there is valid rule
            run_calculation_rules(policy, "PolicyCreatedInvoice", user)
            # run calcrule for creating Bill if there is valid rule
            run_calculation_rules(policy, "PolicyCreated", user)
