from django.db import connection
import xml.etree.ElementTree as ET
from django.core.exceptions import PermissionDenied
import re
from datetime import datetime as py_datetime
import core


@core.comparable
class ByInsureeRequest(object):

    def __init__(self, chf_id, location_id=0):
        self.chf_id = chf_id
        self.location_id = location_id

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class ByInsureeResponseItem(object):

    def __init__(self, product_code, product_name, expiry_date, status,
                 ded_type, ded1, ded2, ceiling1, ceiling2):
        self.product_code = product_code
        self.product_name = product_name
        self.expiry_date = expiry_date
        self.status = status
        self.ded_type = ded_type
        self.ded1 = ded1
        self.ded2 = ded2
        self.ceiling1 = ceiling1
        self.ceiling2 = ceiling2

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
    def _to_item(row):
        if row[7]:
            d = re.split('\D', row[7])
            d.reverse()
            expiry_date = py_datetime(*[int(x) for x in d])
        else:
            expiry_date = None
        return ByInsureeResponseItem(
            product_code=row[5],
            product_name=row[6],
            expiry_date=expiry_date,
            status=row[8],
            ded_type=row[9],
            ded1=row[10],
            ded2=row[11],
            ceiling1=row[12],
            ceiling2=row[13]
        )

    def request(self, by_insuree_request):
        if self.user.is_anonymous or not self.user.has_perm('policy.can_view'):
            raise PermissionDenied
        with connection.cursor() as cur:
            sql = """\
                EXEC [dbo].[uspPolicyInquiry] @CHFID = %s, @LocationId = %s;
            """
            cur.execute(sql, (by_insuree_request.chf_id,
                              by_insuree_request.location_id))
            # stored proc outputs several results (varying from ),
            # we are only interested in the last one
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
                map(lambda x: ByInsureeService._to_item(x), res)
            )
            return ByInsureeResponse(
                by_insuree_request=by_insuree_request,
                items=items
            )


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
        if self.user.is_anonymous or not self.user.has_perm('policy.can_view'):
            raise PermissionDenied
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
