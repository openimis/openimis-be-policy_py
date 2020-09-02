from dataclasses import dataclass

from core.apps import CoreConfig
from django.db import connection
from django.db.models import Sum
from django.db.models.functions import Coalesce
from graphene.utils.str_converters import to_snake_case
from datetime import datetime as py_datetime
from insuree.models import Insuree, Family
from django.db.models import Q
import core
from django.template import Template, Context
from insuree.services import create_insuree_renewal_detail
from policy.apps import PolicyConfig

from .models import Policy, PolicyRenewal
import logging

logger = logging.getLogger(__name__)


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
        family = Family.objects.get(uuid=by_family_request.family_uuid)
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
                is_item_ok=is_item_ok is True,
                is_service_ok=is_service_ok is True
            )


def insert_renewals(date_from=None, date_to=None, officer_id=None, reminding_interval=None, location_id=None, location_levels=4):
    if reminding_interval is None:
        reminding_interval = PolicyConfig.policy_renewal_interval
    from core import datetime
    now = datetime.datetime.now()
    policies = Policy.objects.filter(
        status__in=[Policy.STATUS_EXPIRED, Policy.STATUS_ACTIVE],
        validity_to__isnull=True,
    )
    if reminding_interval:
        policies = policies.filter(expiry_date__lte=now + core.datetimedelta(days=reminding_interval))
    if location_id:
        # TODO support the various levels
        policies = policies.filter(
            Q(family__location_id=location_id)  # Village
            | Q(family__location__parent_id=location_id)  # Ward
            | Q(family__location__parent__parent_id=location_id)  # District
            | Q(family__location__parent__parent__parent_id=location_id)  # Region
        )
    if officer_id:
        policies = policies.filter(officer_id=officer_id)
    if date_from:
        policies = policies.filter(expiry_date__gte=date_from)
    if date_to:
        policies = policies.filter(expiry_date__lte=date_to)

    policies = policies.prefetch_related("product")

    for policy in policies:
        renewal_warning = 0
        renewal_date = policy.expiry_date + core.datetimedelta(days=1)
        product = policy.product  # will be updated if there is a conversion product
        officer = policy.officer
        # Get product code or substitution
        if not product.conversion_product_id:
            previous_products = []
            # Could also add a len(previous_products) < 20 but this avoids loops in the conversion_products
            while product not in previous_products and product.conversion_product:
                previous_products.append(product)
                product = product.conversion_product
            if product in previous_products:
                logger.error("The product %s has a substitution chain with a loop: %s, continuing with %s",
                             policy.product_id, [p.id for p in previous_products], product.id)

        # TODO allow this kind of comparison where the left side is a datetime
        # if datetime.datetime(product.date_from) <= renewal_date <= product.date_to:
        # noinspection PyChainedComparisons
        if renewal_date >= product.date_from and renewal_date <= product.date_to:
            renewal_warning |= 1

        # This is from the original code but is actually not possible as we have an inner join on it
        if not policy.officer_id:
            renewal_warning |= 2
        else:
            if officer:
                previous_officers = []
                while officer not in previous_officers and officer.substitution_officer:
                    previous_officers.append(officer)
                    officer = officer.substitution_officer
                if officer in previous_officers:
                    logger.error("The product %s has a substitution chain with a loop: %s, continuing with %s",
                                 policy.officer_id, [o.id for o in previous_officers], officer.id)
            if officer.works_to and renewal_date > officer.works_to:
                renewal_warning |= 4

        # Check if the policy has another following policy
        following_policies = Policy.objects.filter(family_id=policy.family_id)\
            .filter(Q(product_id=policy.product_id) | Q(product_id=product.id))\
            .filter(start_date__gte=renewal_date)
        if not following_policies.first():
            policy_renewal, policy_renewal_created = PolicyRenewal.objects.get_or_create(
                policy=policy,
                validity_to=None,
                defaults=dict(
                    renewal_prompt_date=now,
                    renewal_date=renewal_date,
                    new_officer=officer,
                    phone_number=officer.phone,
                    sms_status=0,
                    insuree=policy.family.head_insuree,
                    policy=policy,
                    new_product=product,
                    renewal_warnings=renewal_warning,
                    validity_from=now,
                    audit_user_id=0,
                )
            )
            if policy_renewal_created:
                create_insuree_renewal_detail(policy_renewal)  # The insuree module can create additional renewal data


def update_renewals():
    from core import datetime
    now = datetime.datetime.now()
    updated_policies = Policy.objects.filter(validity_to__isnull=True, expiry_date__lt=now) \
        .update(status=Policy.STATUS_EXPIRED)
    logger.debug("update_renewals set %s policies to expired status", updated_policies)
    return updated_policies


@dataclass
class SmsQueueItem:
    index: int
    phone: str
    sms_message: str


def policy_renewal_sms(family_message_template, range_from=None, range_to=None, sms_header_template=None):
    if sms_header_template is None:
        sms_header_template = """--Renewal--
{{renewal.renewal_date}}
{{renewal.insuree.chf_id}}
{{renewal.last_name}} {{renewal.other_names}}
{{district_name|default_if_none:"district?"}}
{{ward_name|default_if_none:"ward?"}}
{{village_name|default_if_none:"village?"}}
{{renewal.new_product.code}}-{{renewal.new_product.name}}
{% for detail in renewal.details.all %}{% if detail.insuree.is_head_of_family %}
HOF{% endif %}
{{detail.insuree.chf_id}}
{{detail.insuree.last_name}} {{detail.insuree.other_names}}
{% endfor %}
"""
    sms_header = Template(sms_header_template)
    family_message = Template(family_message_template)
    from core import datetime
    now = datetime.datetime.now()
    sms_queue = []
    i_count = 0  # TODO: remove and make this method a generator

    if not range_from:
        range_from = now
    if not range_to:
        range_to = now

    renewals = PolicyRenewal.objects.filter(phone_number__isnull=False)\
        .filter(renewal_prompt_date__gte=range_from)\
        .filter(renewal_prompt_date__lte=range_to)\
        .prefetch_related("insuree")\
        .prefetch_related("new_officer")\
        .prefetch_related("new_product")\
        .prefetch_related("details")\
        .prefetch_related("details__insuree")

    for renewal in renewals:
        # Leaving the original code in comment to show it used to be handled. It is now delegated to the Django
        # template for the SMS, we just provide the list of renewal details
        #
        # first get the photo renewal string
        # for detail in renewal.details.filter(validity_to__isnull=True):
        #     if detail.insuree.chf_id == renewal.insuree.chf_id:  # not sure it's equivalent to checking the id
        #         head_photo_renewal = True
        #     else:
        #         sms_photos += f"\n{detail.insuree.chf_id}\n{detail.insuree.last_name} {detail.insuree.other_names}"
        # if len(sms_photos) > 0 or head_photo_renewal:
        #     head_text = "\nHOF" if head_photo_renewal else ""
        #     sms_photos += f"--Photos--{head_text}{sms_photos}" # added to sms_header

        village = renewal.policy.family.location
        sms_header_context = Context(dict(
            renewal=renewal,
            district_name=village.parent.parent if village and village.parent else None,
            ward_name=village.parent if village else None,
            village_name=village,
        ))
        sms_header_text = sms_header.render(sms_header_context)
        sms_message = sms_header_text

        if renewal.new_officer.phone_communication:
            sms_queue.append(SmsQueueItem(i_count, renewal.new_officer.phone, sms_message))
            i_count += 1

        # Create SMS for the family
        if family_message and renewal.insuree.phone:
            expiry_date = renewal.renewal_date - core.datetimedelta(days=1)
            new_family_message = family_message.render(Context(dict(
                insuree=renewal.insuree,
                renewal=renewal,
                expiry_date=expiry_date,
            )))
            #new_family_message = "" # REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(@FamilyMessage, '@@InsuranceID', @CHFID), '@@LastName', @InsLastName),
            # '@@OtherNames', @InsOtherNames), '@@ProductCode', @ProductCode), '@@ProductName', @ProductName),
            # '@@ExpiryDate', FORMAT(@ExpiryDate,'dd MMM yyyy'))

            if new_family_message:
                sms_queue.append(SmsQueueItem(i_count, renewal.insuree.phone, new_family_message))
                i_count += 1

    return sms_queue
