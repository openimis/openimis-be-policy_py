from uuid import uuid4

from django.test import TestCase

from contribution_plan.tests.helpers import create_test_contribution_plan
from policy.models import Policy
from policy.utils import get_contribution_plan_uuid


class InMemoryPolicy:
    """
    Policy as built by the `policyValues` query: not saved, and holding the contribution plan
    uuid instead of a foreign key.
    """

    def __init__(self, contribution_plan):
        self.contribution_plan = contribution_plan


class GetContributionPlanUuidTestCase(TestCase):

    def test_policy_with_a_contribution_plan_instance(self):
        contribution_plan = create_test_contribution_plan()
        # a policy loaded from the database exposes the ContributionPlan instance on the
        # relation and its uuid on the foreign key value
        policy = Policy(contribution_plan=contribution_plan)

        self.assertEqual(
            get_contribution_plan_uuid(policy), contribution_plan.id
        )

    def test_policy_with_a_contribution_plan_uuid(self):
        contribution_plan_uuid = str(uuid4())

        self.assertEqual(
            get_contribution_plan_uuid(InMemoryPolicy(contribution_plan_uuid)),
            contribution_plan_uuid,
        )

    def test_policy_with_an_unsaved_contribution_plan_instance(self):
        class UnsavedContributionPlan:
            id = uuid4()

        contribution_plan = UnsavedContributionPlan()

        self.assertEqual(
            get_contribution_plan_uuid(InMemoryPolicy(contribution_plan)),
            contribution_plan.id,
        )

    def test_policy_without_a_contribution_plan(self):
        self.assertFalse(get_contribution_plan_uuid(Policy()))
        self.assertFalse(get_contribution_plan_uuid(InMemoryPolicy(None)))
