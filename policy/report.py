from policy.reports import policy_renewals
from policy.reports.policy_renewals import policy_renewals_query

report_definitions = [
    {
        "name": "policy_renewals",
        "engine": 0,
        "default_report": policy_renewals.template,
        "description": "Policy renewals",
        "module": "policy",
        "python_query": policy_renewals_query,
        "permission": ["131217"],
    },
]
