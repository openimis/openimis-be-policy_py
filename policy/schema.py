import graphene
from django.core.exceptions import PermissionDenied
from .services import ByInsureeRequest, ByInsureeService
from .services import ByFamilyRequest, ByFamilyService
from .services import EligibilityRequest, EligibilityService
from .apps import PolicyConfig
from django.utils.translation import gettext as _

# We do need all queries and mutations in the namespace here.
from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutations import *  # lgtm [py/polluting-import]


class Query(graphene.ObjectType):
    # Note:
    # A Policy is bound to a Family...
    # but an insuree of the family is only covered by the family policy
    # if there is a (valid) InsureePolicy
    policies_by_insuree = graphene.relay.ConnectionField(
        PolicyByFamilyOrInsureeConnection,
        chf_id=graphene.String(required=True),
        active_or_last_expired_only=graphene.Boolean(),
        show_history=graphene.Boolean(),
        order_by=graphene.String(),
    )
    policies_by_family = graphene.relay.ConnectionField(
        PolicyByFamilyOrInsureeConnection,
        family_uuid=graphene.String(required=True),
        active_or_last_expired_only=graphene.Boolean(),
        show_history=graphene.Boolean(),
        order_by=graphene.String(),
    )
    # TODO: refactoring
    # Eligibility is calculated for a Policy... which is bound to a Family (not an Insuree)
    # YET: family member may not be covered by the policy!!
    # This requires to refactor the EligibilityService
    policy_eligibility_by_insuree = graphene.Field(
        EligibilityGQLType,
        chfId=graphene.String(required=True)
    )
    policy_item_eligibility_by_insuree = graphene.Field(
        EligibilityGQLType,
        chfId=graphene.String(required=True),
        itemCode=graphene.String(required=True)
    )
    policy_service_eligibility_by_insuree = graphene.Field(
        EligibilityGQLType,
        chfId=graphene.String(required=True),
        serviceCode=graphene.String(required=True),
    )

    @staticmethod
    def _to_policy_by_family_or_insuree_item(item):
        return PolicyByFamilyOrInsureeGQLType(
            policy_id=item.policy_id,
            policy_uuid=item.policy_uuid,
            policy_value=item.policy_value,
            product_code=item.product_code,
            product_name=item.product_name,
            start_date=item.start_date,
            enroll_date=item.enroll_date,
            effective_date=item.effective_date,
            expiry_date=item.expiry_date,
            officer_code=item.officer_code,
            officer_name=item.officer_name,
            status=item.status,
            ded=item.ded,
            ded_in_patient=item.ded_in_patient,
            ded_out_patient=item.ded_out_patient,
            ceiling=item.ceiling,
            ceiling_in_patient=item.ceiling_in_patient,
            ceiling_out_patient=item.ceiling_out_patient,
            balance=item.balance,
            validity_from=item.validity_from,
            validity_to=item.validity_to
        )

    def resolve_policies_by_insuree(self, info, **kwargs):
        if not info.context.user.has_perms(PolicyConfig.gql_query_policies_by_insuree_perms):
            raise PermissionDenied(_("unauthorized"))
        req = ByInsureeRequest(
            chf_id=kwargs.get('chf_id'),
            active_or_last_expired_only=kwargs.get('active_or_last_expired_only', False),
            show_history=kwargs.get('show_history', False),
            order_by=kwargs.get('order_by', None)
        )
        res = ByInsureeService(user=info.context.user).request(req)
        return [Query._to_policy_by_family_or_insuree_item(x) for x in res.items]

    def resolve_policies_by_family(self, info, **kwargs):
        if not info.context.user.has_perms(PolicyConfig.gql_query_policies_by_family_perms):
            raise PermissionDenied(_("unauthorized"))
        req = ByFamilyRequest(
            family_uuid=kwargs.get('family_uuid'),
            active_or_last_expired_only=kwargs.get('active_or_last_expired_only', False),
            show_history=kwargs.get('show_history', False),
            order_by=kwargs.get('order_by', None)
        )
        res = ByFamilyService(user=info.context.user).request(req)
        return [Query._to_policy_by_family_or_insuree_item(x) for x in res.items]

    @staticmethod
    def _resolve_policy_eligibility_by_insuree(user, req):
        res = EligibilityService(user=user).request(req)
        return EligibilityGQLType(
            prod_id=res.prod_id,
            total_admissions_left=res.total_admissions_left,
            total_visits_left=res.total_visits_left,
            total_consultations_left=res.total_consultations_left,
            total_surgeries_left=res.total_surgeries_left,
            total_deliveries_left=res.total_deliveries_left,
            total_antenatal_left=res.total_antenatal_left,
            consultation_amount_left=res.consultation_amount_left,
            surgery_amount_left=res.surgery_amount_left,
            delivery_amount_left=res.delivery_amount_left,
            hospitalization_amount_left=res.hospitalization_amount_left,
            antenatal_amount_left=res.antenatal_amount_left,
            min_date_service=res.min_date_service,
            min_date_item=res.min_date_item,
            service_left=res.service_left,
            item_left=res.item_left,
            is_item_ok=res.is_item_ok,
            is_service_ok=res.is_service_ok
        )

    def resolve_policy_eligibility_by_insuree(self, info, **kwargs):
        if not info.context.user.has_perms(PolicyConfig.gql_query_eligibilities_perms):
            raise PermissionDenied(_("unauthorized"))
        req = EligibilityRequest(
            chf_id=kwargs.get('chfId')
        )
        return Query._resolve_policy_eligibility_by_insuree(
            user=info.context.user,
            req=req
        )

    def resolve_policy_item_eligibility_by_insuree(self, info, **kwargs):
        if not info.context.user.has_perms(PolicyConfig.gql_query_eligibilities_perms):
            raise PermissionDenied(_("unauthorized"))
        req = EligibilityRequest(
            chf_id=kwargs.get('chfId'),
            item_code=kwargs.get('itemCode')
        )
        return Query._resolve_policy_eligibility_by_insuree(
            user=info.context.user,
            req=req
        )

    def resolve_policy_service_eligibility_by_insuree(self, info, **kwargs):
        if not info.context.user.has_perms(PolicyConfig.gql_query_eligibilities_perms):
            raise PermissionDenied(_("unauthorized"))
        req = EligibilityRequest(
            chf_id=kwargs.get('chfId'),
            service_code=kwargs.get('serviceCode')
        )
        return Query._resolve_policy_eligibility_by_insuree(
            user=info.context.user,
            req=req
        )
