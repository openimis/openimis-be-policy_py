from .apps import PolicyConfig
from core.signals import Signal
from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal

_check_formal_sector_for_policy_signal_params = ["user", "policy_id"]
signal_check_formal_sector_for_policy = Signal(_check_formal_sector_for_policy_signal_params)
