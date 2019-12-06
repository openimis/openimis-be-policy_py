from django.db import connection
from django.db.models import Q
import xml.etree.ElementTree as ET
import re
from datetime import datetime as py_datetime
import core
from .models import Policy
from product.models import Product
from contribution.services import ByPolicyPremiumsAmountService


# --- BY INSUREE ---
# TODO: should become "BY FAMILY":
# A Policy is bound to a Family
# ... and should not make any assumption on what a Family looks like!
# -------------------
@core.comparable
class ByInsureeRequest(object):

    def __init__(self, chf_id):
        self.chf_id = chf_id

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class ByInsureeResponseItem(object):

    def __init__(self, product_code, product_name, expiry_date, status,
                 ded, ded_in_patient, ded_out_patient, ceiling, ceiling_in_patient, ceiling_out_patient):
        self.product_code = product_code
        self.product_name = product_name
        self.expiry_date = expiry_date
        self.status = status
        self.ded = ded
        self.ded_in_patient = ded_in_patient
        self.ded_out_patient = ded_out_patient
        self.ceiling = ceiling
        self.ceiling_in_patient = ceiling_in_patient
        self.ceiling_out_patient = ceiling_out_patient

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class ByInsureeResponse(object):

    def __init__(self, by_insuree_request, items):
        self.by_insuree_request = by_insuree_request
        self.items = items

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


class ByInsureeService(object):

    def __init__(self, user):
        self.user = user

    @staticmethod
    def _to_item(cols, row):
        return ByInsureeResponseItem(
            product_code=row[7],
            product_name=row[8],
            expiry_date=row[6],
            status=row[5],
            ded=row[cols.index('Deductable')
                    ] if 'Deductable' in cols else None,
            ded_in_patient=row[cols.index(
                'IP Deductable')] if 'IP Deductable' in cols else None,
            ded_out_patient=row[cols.index(
                'OP Deductable')] if 'OP Deductable' in cols else None,
            ceiling=row[cols.index('Ceiling')] if 'Ceiling' in cols else None,
            ceiling_in_patient=row[cols.index(
                'IP Ceiling')] if 'IP Ceiling' in cols else None,
            ceiling_out_patient=row[cols.index(
                'OP Ceiling')] if 'OP Ceiling' in cols else None
        )

    def request(self, by_insuree_request):
        with connection.cursor() as cur:
            sql = """\
                EXEC [dbo].[uspPolicyInquiry2] @CHFID = %s;
            """
            cur.execute(sql, [by_insuree_request.chf_id])
            # stored proc outputs several results (varying from ),
            # we are only interested in the last one
            cols = [col[0] for col in cur.description]
            next = True
            res = []
            while next:
                try:
                    res = cur.fetchall()
                except:
                    pass
                finally:
                    next = cur.nextset()
            items = tuple(
                map(lambda x: ByInsureeService._to_item(cols, x), res)
            )
            return ByInsureeResponse(
                by_insuree_request=by_insuree_request,
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

    def __init__(self, eligibility_request, prod_id=None, total_admissions_left=0, total_visits_left=0, total_consultations_left=0, total_surgeries_left=0,
                 total_deliveries_left=0, total_antenatal_left=0, consultation_amount_left=0, surgery_amount_left=0, delivery_amount_left=0,
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
             total_deliveries_left, total_antenatal_left, consultation_amount_left, surgery_amount_left, delivery_amount_left,
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
