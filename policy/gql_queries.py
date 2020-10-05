import graphene
from graphene_django import DjangoObjectType
from .models import Policy
from core import prefix_filterset, filter_validity, ExtendedConnection, ExtendedRelayConnection


class PolicyGQLType(DjangoObjectType):
    class Meta:
        model = Policy
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "uuid": ["exact"],
        }
        connection_class = ExtendedConnection


class PolicyByFamilyOrInsureeGQLType(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node,)

    policy_id = graphene.Int()
    policy_uuid = graphene.String()
    policy_value = graphene.Float()
    product_code = graphene.String()
    product_name = graphene.String()
    start_date = graphene.Date()
    enroll_date = graphene.Date()
    effective_date = graphene.Date()
    expiry_date = graphene.Date()
    officer_code = graphene.String()
    officer_name = graphene.String()
    status = graphene.String()
    ded = graphene.Float()
    ded_in_patient = graphene.Float()
    ded_out_patient = graphene.Float()
    ceiling = graphene.Float()
    ceiling_in_patient = graphene.Float()
    ceiling_out_patient = graphene.Float()
    balance = graphene.Float()
    validity_from = graphene.Date()
    validity_to = graphene.Date()


class PolicyByFamilyOrInsureeConnection(ExtendedRelayConnection):
    class Meta:
        node = PolicyByFamilyOrInsureeGQLType


class EligibilityGQLType(graphene.ObjectType):
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

