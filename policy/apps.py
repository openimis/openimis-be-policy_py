from django.apps import AppConfig
from django.conf import settings

MODULE_NAME = "policy"

DEFAULT_CFG = {
    "gql_query_policies_by_insuree_perms": [],
    "gql_query_policies_by_family_perms": [],
    "gql_query_eligibilities_perms": [],
    "policy_renewal_interval": 14,  # Notify renewal nb of days before expiry date
}


class PolicyConfig(AppConfig):
    name = MODULE_NAME

    gql_query_policies_by_insuree_perms = []
    gql_query_policies_by_family_perms = []
    gql_query_eligibilities_perms = []
    policy_renewal_interval = 14

    def _configure_permissions(self, cfg):
        PolicyConfig.gql_query_policies_by_insuree_perms = cfg["gql_query_policies_by_insuree_perms"]
        PolicyConfig.gql_query_policies_by_family_perms = cfg["gql_query_policies_by_family_perms"]
        PolicyConfig.gql_query_eligibilities_perms = cfg["gql_query_eligibilities_perms"]

    def _configure_renewal(self, cfg):
        PolicyConfig.policy_renewal_interval = cfg["policy_renewal_interval"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
        self._configure_renewal(cfg)
