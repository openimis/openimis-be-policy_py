import graphene
from graphene_django import DjangoObjectType
from .models import Policy
from .services import ByInsureeRequest, ByInsureeResponse, ByInsureeService
from .services import BalanceRequest, BalanceResponse, BalanceService
from .services import EligibilityRequest, EligibilityService


class PolicyByInsureeItemGraphQLType(graphene.ObjectType):
    # policy_id = graphene.Int()
    # policy_value = graphene.Float()
    # premiums_amount = graphene.Float()
    # balance = graphene.Float()
    product_code = graphene.String()
    product_name = graphene.String()
    expiry_date = graphene.Date()
    status = graphene.String()
    ded_type = graphene.String()
    ded1 = graphene.Float()
    ded2 = graphene.Float()
    ceiling1 = graphene.Float()
    ceiling2 = graphene.Float()


class PolicyBalanceGraphQLType(graphene.ObjectType):
    family_id = graphene.Int()
    product_code = graphene.String()
    policy_id = graphene.Int()
    policy_value = graphene.Float()
    premiums_amount = graphene.Float()
    balance = graphene.Float()


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
    policy_balance = graphene.Field(
        PolicyBalanceGraphQLType,
        familyId=graphene.Int(required=True),
        productCode=graphene.String(required=True)
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
            # policy_id=item.policy_id,
            # policy_value=item.policy_value,
            # premiums_amount=item.premiums_amount,
            # balance=item.balance,
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
            family_id=kwargs.get('familyId'),
            location_id=kwargs.get('locationId') or 0
        )
        res = ByInsureeService(user=info.context.user).request(req)
        return PoliciesByInsureeGraphQLType(
            items=tuple(map(
                lambda x: Query._to_policy_by_insuree_item(x), res.items))
        )

    def resolve_policy_balance(self, info, **kwargs):
        family_id = kwargs.get('familyId')
        product_code = kwargs.get('productCode')
        req = BalanceRequest(
            family_id=family_id,
            product_code=product_code
        )
        res = BalanceService(user=info.context.user).request(req)
        return PolicyBalanceGraphQLType(
            family_id=family_id,
            product_code=product_code,
            policy_id=res.policy_id,
            policy_value=res.policy_value,
            premiums_amount=res.premiums_amount,
            balance=res.balance
        )

    @staticmethod
    def _resolve_policy_eligibility_by_insuree(user, req):
        res = EligibilityService(user=user).request(req)
        return EligibilityGraphQLType(
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
