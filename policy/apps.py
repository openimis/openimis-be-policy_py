from django.apps import AppConfig

MODULE_NAME = "policy"

DEFAULT_CFG = {
    "gql_query_policies_by_insuree_perms": [],
    "gql_query_eligibilities_perms": []
}


class PolicyConfig(AppConfig):
    name = MODULE_NAME

    gql_query_policies_by_insuree_perms = []
    gql_query_eligibilities_perms = []

    def _configure_permissions(self, cfg):
        PolicyConfig.gql_query_policies_by_insuree_perms = cfg["gql_query_policies_by_insuree_perms"]
        PolicyConfig.gql_query_eligibilities_perms = cfg["gql_query_eligibilities_perms"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
