from django.apps import AppConfig
from django.conf import settings

MODULE_NAME = "policy"

DEFAULT_CFG = {
    "gql_query_policies_by_insuree_perms": [],
    "gql_query_policies_by_family_perms": [],
    "gql_query_eligibilities_perms": []
    "policy_renewal_interval": 14,  # Notify renewal nb of days before expiry date
    "policy_renewal_photo_age_adult": 60,  # age (in months) of a picture due for renewal for adults
    "policy_renewal_photo_age_child": 12,  # age (in months) of a picture due for renewal for children
}


class PolicyConfig(AppConfig):
    name = MODULE_NAME

    gql_query_policies_by_insuree_perms = []
    gql_query_policies_by_family_perms = []
    gql_query_eligibilities_perms = []
    policy_renewal_interval = 14
    policy_renewal_photo_age_adult = 60
    policy_renewal_photo_age_child = 12

    def _configure_permissions(self, cfg):
        PolicyConfig.gql_query_policies_by_insuree_perms = cfg["gql_query_policies_by_insuree_perms"]
        PolicyConfig.gql_query_policies_by_family_perms = cfg["gql_query_policies_by_family_perms"]
        PolicyConfig.gql_query_eligibilities_perms = cfg["gql_query_eligibilities_perms"]
        PolicyConfig.policy_renewal_interval = cfg["policy_renewal_interval"]
        PolicyConfig.policy_renewal_photo_age_adult = cfg["policy_renewal_photo_age_adult"]
        PolicyConfig.policy_renewal_photo_age_child = cfg["policy_renewal_photo_age_child"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
