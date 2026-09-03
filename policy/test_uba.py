"""
UBA coverage for the policy module: the ENROLMENT credential, held on a village.

A policy has no location of its own - the TODO that sat in `Policy.get_queryset` asked how
to reach one - so it is filtered through the family it covers, whose own location is a
village. Row security was simply absent here before, so these tests also pin down the
district filter that now applies.
"""
from django.core.cache import cache
from django.test import TestCase

from core.apps import ENROLMENT_UBA_LINK_TYPE
from core.services.userServices import create_or_update_user_districts
from core.test_helpers import (
    create_test_interactive_user,
    create_test_role,
    create_test_user_business_access,
)
from location.models import Location
from location.test_helpers import create_test_village
from policy.apps import PolicyConfig
from policy.models import Policy
from policy.test_helpers import create_test_policy2
from product.test_helpers import create_test_product


class EnrolmentUbaPolicyRowSecurityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        from insuree.test_helpers import create_test_insuree

        cls.linked_village = create_test_village({"name": "UbaPolLinked"})
        cls.district = cls.linked_village.parent.parent
        cls.other_village = Location.objects.create(
            name="UbaPolOther", code="UBAPO2", type="V",
            parent=cls.linked_village.parent, audit_user_id=-1, validity_from="2019-01-01")

        cls.role = create_test_role(
            name="UBA policy", uba_rights=[int(PolicyConfig.gql_query_policies_perms[0])])
        cls.officer_user = create_test_interactive_user(
            username="ubapolofficer", roles=[cls.role.id])
        cls.plain_user = create_test_interactive_user(
            username="ubapolplain", roles=[cls.role.id])
        for user in (cls.officer_user, cls.plain_user):
            create_or_update_user_districts(user.i_user, [cls.district.id], -1)

        create_test_user_business_access(
            user=cls.officer_user,
            business_object=cls.linked_village,
            link_type=ENROLMENT_UBA_LINK_TYPE,
        )

        product = create_test_product("UBAP")
        cls.linked_insuree = create_test_insuree(
            custom_props={"chf_id": "UBAPI001", "current_village": cls.linked_village},
            family_custom_props={"location": cls.linked_village})
        cls.other_insuree = create_test_insuree(
            custom_props={"chf_id": "UBAPI002", "current_village": cls.other_village},
            family_custom_props={"location": cls.other_village})
        cls.linked_policy = create_test_policy2(product, cls.linked_insuree)
        cls.other_policy = create_test_policy2(product, cls.other_insuree)

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _policies_for(self, user):
        return set(
            Policy.get_queryset(
                Policy.objects.filter(
                    id__in=[self.linked_policy.id, self.other_policy.id]), user
            ).values_list("id", flat=True)
        )

    def test_policies_are_narrowed_to_the_linked_village(self):
        self.assertEqual({self.linked_policy.id}, self._policies_for(self.officer_user))

    def test_a_user_without_a_link_keeps_the_district_scope(self):
        self.assertEqual(
            {self.linked_policy.id, self.other_policy.id}, self._policies_for(self.plain_user))

    def test_a_second_link_widens_to_both_villages(self):
        create_test_user_business_access(
            user=self.officer_user,
            business_object=self.other_village,
            link_type=ENROLMENT_UBA_LINK_TYPE,
        )
        self.assertEqual(
            {self.linked_policy.id, self.other_policy.id},
            self._policies_for(self.officer_user))

    def test_the_graphql_type_routes_through_the_model(self):
        # PolicyGQLType had no get_queryset at all, so the model rule was never reached
        # from GraphQL while the REST/FHIR API did apply it
        from policy.gql_queries import PolicyGQLType

        self.assertTrue(hasattr(PolicyGQLType, "get_queryset"))
        visible = PolicyGQLType.get_queryset(
            Policy.objects.filter(id__in=[self.linked_policy.id, self.other_policy.id]),
            self.officer_user)
        self.assertEqual({self.linked_policy.id}, set(visible.values_list("id", flat=True)))
