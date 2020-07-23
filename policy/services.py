from django.db import connection
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from graphene.utils.str_converters import to_snake_case
import xml.etree.ElementTree as ET
import re
from datetime import datetime as py_datetime
import core
from .models import Policy
from product.models import Product
from insuree.models import Insuree, Family


@core.comparable
class ByInsureeRequest(object):

    def __init__(self, chf_id, active_or_last_expired_only=False, show_history=False, order_by=None):
        self.chf_id = chf_id
        self.active_or_last_expired_only = active_or_last_expired_only
        self.show_history = show_history
        self.order_by = order_by

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class ByFamilyOrInsureeResponseItem(object):

    def __init__(self,
                 policy_id,
                 policy_uuid,
                 policy_value,
                 product_code,
                 product_name,
                 start_date,
                 enroll_date,
                 effective_date,
                 expiry_date,
                 officer_code,
                 officer_name,
                 status,
                 ded,
                 ded_in_patient,
                 ded_out_patient,
                 ceiling,
                 ceiling_in_patient,
                 ceiling_out_patient,
                 balance,
                 validity_from,
                 validity_to
                 ):
        self.policy_id = policy_id
        self.policy_uuid = policy_uuid
        self.policy_value = policy_value
        self.product_code = product_code
        self.product_name = product_name
        self.start_date = start_date
        self.enroll_date = enroll_date
        self.effective_date = effective_date
        self.expiry_date = expiry_date
        self.officer_code = officer_code
        self.officer_name = officer_name
        self.status = status
        self.ded = ded
        self.ded_in_patient = ded_in_patient
        self.ded_out_patient = ded_out_patient
        self.ceiling = ceiling
        self.ceiling_in_patient = ceiling_in_patient
        self.ceiling_out_patient = ceiling_out_patient
        self.balance = balance
        self.validity_from = validity_from
        self.validity_to = validity_to

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class ByInsureeResponse(object):

    def __init__(self, by_insuree_request, items):
        self.by_insuree_request = by_insuree_request
        self.items = items

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

class FilteredPoliciesService(object):

    def __init__(self, user):
        self.user = user

    @staticmethod
    def _to_item(row):
        return ByFamilyOrInsureeResponseItem(
            policy_id=row.id,
            policy_uuid=row.uuid,
            policy_value=row.value,
            product_code=row.product.code,
            product_name=row.product.name,
            start_date=row.start_date,
            enroll_date=row.enroll_date,
            effective_date=row.effective_date,
            expiry_date=row.expiry_date,
            officer_code=row.officer.code,
            officer_name=row.officer.name(),
            status=row.status,
            ded=row.total_ded_g,
            ded_in_patient=row.total_ded_ip,
            ded_out_patient=row.total_ded_op,
            ceiling=0,  # TODO: product.xxx
            ceiling_in_patient=0,  # TODO: product.xxx
            ceiling_out_patient=0,  # TODO: product.xxx
            balance=0,  # TODO: nullsafe calculation from value,...
            validity_from=row.validity_from,
            validity_to=row.validity_to
        )

    def build_query(self, req):
        # TODO: prevent direct dependency on claim_ded structure?
        res = Policy.objects \
            .select_related('product') \
            .select_related('officer') \
            .prefetch_related('claim_ded_rems') \
            .annotate(total_ded_g=Sum('claim_ded_rems__ded_g')) \
            .annotate(total_ded_ip=Sum('claim_ded_rems__ded_ip')) \
            .annotate(total_ded_op=Sum('claim_ded_rems__ded_op')) \
            .annotate(total_rem_g=Sum('claim_ded_rems__rem_g')) \
            .annotate(total_rem_op=Sum('claim_ded_rems__rem_op')) \
            .annotate(total_rem_ip=Sum('claim_ded_rems__rem_ip')) \
            .annotate(total_rem_consult=Sum('claim_ded_rems__rem_consult')) \
            .annotate(total_rem_surgery=Sum('claim_ded_rems__rem_surgery')) \
            .annotate(total_rem_delivery=Sum('claim_ded_rems__rem_delivery')) \
            .annotate(total_rem_hospitalization=Sum('claim_ded_rems__rem_hospitalization')) \
            .annotate(total_rem_antenatal=Sum('claim_ded_rems__rem_antenatal'))
        if not req.show_history:
            res = res.filter(*core.filter_validity())
        if req.active_or_last_expired_only:
            # sort on status, so that any active policy (status = 2) pops up...
            res = res.annotate(not_null_expiry_date=Coalesce('expiry_date', py_datetime.max)) \
                .annotate(not_null_validity_to=Coalesce('validity_to', py_datetime.max)) \
                .order_by('product__code', 'status', '-not_null_expiry_date', '-not_null_validity_to', '-validity_from')
        return res

class ByInsureeService(FilteredPoliciesService):

    def __init__(self, user):
        super(ByInsureeService, self).__init__(user)

    def request(self, by_insuree_request):
        insurees = Insuree.objects.filter(
            chf_id=by_insuree_request.chf_id,
            *core.filter_validity() if not by_insuree_request.show_history else []
        )
        res = self.build_query(by_insuree_request)
        res = res.prefetch_related('insuree_policies')
        res = res.filter(insuree_policies__insuree__in=insurees)
        # .distinct('product__code') >> DISTINCT ON fields not supported by MS-SQL
        if by_insuree_request.active_or_last_expired_only:
            products = {}
            for r in res:
                if r.product.code not in products.keys():
                    products[r.product.code] = r
            res = products.values()
        items = tuple(
            map(lambda x: FilteredPoliciesService._to_item(x), res)
        )
        # possible improvement: sort via the ORM
        # ... but beware of the active_or_last_expired_only filtering!
        order_attr = to_snake_case(by_insuree_request.order_by if by_insuree_request.order_by else "expiry_date")
        desc = False
        if order_attr.startswith('-'):
            order_attr = order_attr[1:]
            desc = True
        items = sorted(items, key=lambda x: getattr(x, order_attr), reverse=desc)
        return ByInsureeResponse(
            by_insuree_request=by_insuree_request,
            items=items
        )


@core.comparable
class ByFamilyRequest(object):

    def __init__(self, family_uuid, active_or_last_expired_only=False, show_history=False, order_by=None):
        self.family_uuid = family_uuid
        self.active_or_last_expired_only = active_or_last_expired_only
        self.show_history = show_history
        self.order_by = order_by

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class ByFamilyResponse(object):

    def __init__(self, by_family_request, items):
        self.by_family_request = by_family_request
        self.items = items

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


class ByFamilyService(FilteredPoliciesService):
    def __init__(self, user):
        super(ByFamilyService, self).__init__(user)

    def request(self, by_family_request):
        family = Family.objects.get(uuid=by_family_request.family_uuid, *core.filter_validity())
        res = self.build_query(by_family_request)
        res = res.filter(family_id=family.id)
        # .distinct('product__code') >> DISTINCT ON fields not supported by MS-SQL
        if by_family_request.active_or_last_expired_only:
            products = {}
            for r in res:
                if r.product.code not in products.keys():
                    products[r.product.code] = r
            res = products.values()
        items = tuple(
            map(lambda x: FilteredPoliciesService._to_item(x), res)
        )
        return ByFamilyResponse(
            by_family_request=by_family_request,
            items=items
        )


# --- ELIGIBILITY --
# TODO: should become "BY FAMILY":
# Eligibility is calculated from a Policy
# ... which is bound to a Family (same remark as ByInsureeService)
# -------------------
@core.comparable
class EligibilityRequest(object):

    def __init__(self, chf_id, service_code=None, item_code=None):
        self.chf_id = chf_id
        self.service_code = service_code
        self.item_code = item_code

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class EligibilityResponse(object):

    def __init__(self, eligibility_request, prod_id=None, total_admissions_left=0, total_visits_left=0,
                 total_consultations_left=0, total_surgeries_left=0,
                 total_deliveries_left=0, total_antenatal_left=0, consultation_amount_left=0, surgery_amount_left=0,
                 delivery_amount_left=0,
                 hospitalization_amount_left=0, antenatal_amount_left=0,
                 min_date_service=None, min_date_item=None, service_left=0, item_left=0, is_item_ok=0, is_service_ok=0):
        self.eligibility_request = eligibility_request
        self.prod_id = prod_id
        self.total_admissions_left = total_admissions_left
        self.total_visits_left = total_visits_left
        self.total_consultations_left = total_consultations_left
        self.total_surgeries_left = total_surgeries_left
        self.total_deliveries_left = total_deliveries_left
        self.total_antenatal_left = total_antenatal_left
        self.consultation_amount_left = consultation_amount_left
        self.surgery_amount_left = surgery_amount_left
        self.delivery_amount_left = delivery_amount_left
        self.hospitalization_amount_left = hospitalization_amount_left
        self.antenatal_amount_left = antenatal_amount_left
        self.min_date_service = min_date_service
        self.min_date_item = min_date_item
        self.service_left = service_left
        self.item_left = item_left
        self.is_item_ok = is_item_ok
        self.is_service_ok = is_service_ok

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


class EligibilityService(object):

    def __init__(self, user):
        self.user = user

    def request(self, req):
        with connection.cursor() as cur:
            sql = """\
                DECLARE @MinDateService DATE, @MinDateItem DATE,
                        @ServiceLeft INT, @ItemLeft INT,
                        @isItemOK BIT, @isServiceOK BIT;
                EXEC [dbo].[uspServiceItemEnquiry] @CHFID = %s, @ServiceCode = %s, @ItemCode = %s,
                     @MinDateService = @MinDateService, @MinDateItem = @MinDateItem,
                     @ServiceLeft = @ServiceLeft, @ItemLeft = @ItemLeft,
                     @isItemOK = @isItemOK, @isServiceOK = @isServiceOK;
                SELECT @MinDateService, @MinDateItem, @ServiceLeft, @ItemLeft, @isItemOK, @isServiceOK
            """
            cur.execute(sql, (req.chf_id,
                              req.service_code,
                              req.item_code))
            res = cur.fetchone()  # retrieve the stored proc @Result table
            if res is None:
                return EligibilityResponse(eligibility_request=req)

            (prod_id, total_admissions_left, total_visits_left, total_consultations_left, total_surgeries_left,
             total_deliveries_left, total_antenatal_left, consultation_amount_left, surgery_amount_left,
             delivery_amount_left,
             hospitalization_amount_left, antenatal_amount_left) = res
            cur.nextset()
            (min_date_service, min_date_item, service_left,
             item_left, is_item_ok, is_service_ok) = cur.fetchone()
            return EligibilityResponse(
                eligibility_request=req,
                prod_id=prod_id or None,
                total_admissions_left=total_admissions_left or 0,
                total_visits_left=total_visits_left or 0,
                total_consultations_left=total_consultations_left or 0,
                total_surgeries_left=total_surgeries_left or 0,
                total_deliveries_left=total_deliveries_left or 0,
                total_antenatal_left=total_antenatal_left or 0,
                consultation_amount_left=consultation_amount_left or 0.0,
                surgery_amount_left=surgery_amount_left or 0.0,
                delivery_amount_left=delivery_amount_left or 0.0,
                hospitalization_amount_left=hospitalization_amount_left or 0.0,
                antenatal_amount_left=antenatal_amount_left or 0.0,
                min_date_service=min_date_service,
                min_date_item=min_date_item,
                service_left=service_left or 0,
                item_left=item_left or 0,
                is_item_ok=is_item_ok == True,
                is_service_ok=is_service_ok == True
            )
