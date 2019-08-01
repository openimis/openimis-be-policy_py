import graphene
from graphene_django import DjangoObjectType
from .models import Policy
from .services import ByInsureeRequest, ByInsureeResponse, ByInsureeService
from .services import EligibilityRequest, EligibilityService


class PolicyByInsureeItemGraphQLType(graphene.ObjectType):
    product_code = graphene.String()
    product_name = graphene.String()
    expiry_date = graphene.Date()
    status = graphene.String()
    ded_type = graphene.String()
    ded1 = graphene.Float()
    ded2 = graphene.Float()
    ceiling1 = graphene.Float()
    ceiling2 = graphene.Float()


class PoliciesByInsureeGraphQLType(graphene.ObjectType):
    items = graphene.List(PolicyByInsureeItemGraphQLType)


class EligibilityGraphQLType(graphene.ObjectType):
    prod_id = graphene.String()
    total_admissions_left = graphene.Int()
    total_visits_left = graphene.Int()
    total_consultations_left = graphene.Int()
    total_surgeries_left = graphene.Int()
    total_deliveries_left = graphene.Int()
    total_antenatal_left = graphene.Int()
    consultation_amount_left = graphene.Float()
    surgery_amount_left = graphene.Float()
    delivery_amount_left = graphene.Float()
    hospitalization_amount_left = graphene.Float()
    antenatal_amount_left = graphene.Float()
    min_date_service = graphene.types.datetime.Date()
    min_date_item = graphene.types.datetime.Date()
    service_left = graphene.Int()
    item_left = graphene.Int()
    is_item_ok = graphene.Boolean()
    is_service_ok = graphene.Boolean()


class Query(graphene.ObjectType):
    policies_by_insuree = graphene.Field(
        PoliciesByInsureeGraphQLType,
        chfId=graphene.String(required=True),
        locationId=graphene.Int()
    )
    policy_eligibility_by_insuree = graphene.Field(
        EligibilityGraphQLType,
        chfId=graphene.String(required=True)
    )
    policy_item_eligibility_by_insuree = graphene.Field(
        EligibilityGraphQLType,
        chfId=graphene.String(required=True),
        itemCode=graphene.String(required=True)
    )
    policy_service_eligibility_by_insuree = graphene.Field(
        EligibilityGraphQLType,
        chfId=graphene.String(required=True),
        serviceCode=graphene.String(required=True),
    )

    @staticmethod
    def _to_policy_by_insuree_item(item):
        return PolicyByInsureeItemGraphQLType(
            product_code=item.product_code,
            product_name=item.product_name,
            expiry_date=item.expiry_date,
            status=item.status,
            ded_type=item.ded_type,
            ded1=item.ded1,
            ded2=item.ded2,
            ceiling1=item.ceiling1,
            ceiling2=item.ceiling2
        )

    def resolve_policies_by_insuree(self, info, **kwargs):
        req = ByInsureeRequest(
            chf_id=kwargs.get('chfId'),
            location_id=kwargs.get('locationId') or 0
        )
        resp = ByInsureeService(user=info.context.user).request(req)
        return PoliciesByInsureeGraphQLType(
            items=tuple(map(
                lambda x: Query._to_policy_by_insuree_item(x), resp.items))
        )

    @staticmethod
    def _resolve_policy_eligibility_by_insuree(user, req):
        resp = EligibilityService(user=user).request(req)
        return EligibilityGraphQLType(
            prod_id=resp.prod_id,
            total_admissions_left=resp.total_admissions_left,
            total_visits_left=resp.total_visits_left,
            total_consultations_left=resp.total_consultations_left,
            total_surgeries_left=resp.total_surgeries_left,
            total_deliveries_left=resp.total_deliveries_left,
            total_antenatal_left=resp.total_antenatal_left,
            consultation_amount_left=resp.consultation_amount_left,
            surgery_amount_left=resp.surgery_amount_left,
            delivery_amount_left=resp.delivery_amount_left,
            hospitalization_amount_left=resp.hospitalization_amount_left,
            antenatal_amount_left=resp.antenatal_amount_left,
            min_date_service=resp.min_date_service,
            min_date_item=resp.min_date_item,
            service_left=resp.service_left,
            item_left=resp.item_left,
            is_item_ok=resp.is_item_ok,
            is_service_ok=resp.is_service_ok
        )

    def resolve_policy_eligibility_by_insuree(self, info, **kwargs):
        req = EligibilityRequest(
            chf_id=kwargs.get('chfId')
        )
        return Query._resolve_policy_eligibility_by_insuree(
            user=info.context.user,
            req=req
        )

    def resolve_policy_item_eligibility_by_insuree(self, info, **kwargs):
        req = EligibilityRequest(
            chf_id=kwargs.get('chfId'),
            item_code=kwargs.get('itemCode')
        )
        return Query._resolve_policy_eligibility_by_insuree(
            user=info.context.user,
            req=req
        )

    def resolve_policy_service_eligibility_by_insuree(self, info, **kwargs):
        req = EligibilityRequest(
            chf_id=kwargs.get('chfId'),
            service_code=kwargs.get('serviceCode')
        )
        return Query._resolve_policy_eligibility_by_insuree(
            user=info.context.user,
            req=req
        )
