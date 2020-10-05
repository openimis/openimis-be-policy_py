from unittest import mock

from core.models import InteractiveUser, User
from core.test_helpers import create_test_officer
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from insuree.test_helpers import create_test_insuree, create_test_photo
from medical.test_helpers import create_test_item
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product

from .services import *


class EligibilityServiceTestCase(TestCase):
    def test_eligibility_request_permission_denied(self):
        with mock.patch("django.db.backends.utils.CursorWrapper") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.description = None
            mock_user = mock.Mock(is_anonymous=False)
            mock_user.has_perm = mock.MagicMock(return_value=False)
            req = EligibilityRequest(chf_id="a")
            service = EligibilityService(mock_user)
            with self.assertRaises(PermissionDenied) as cm:
                service.request(req)
            mock_user.has_perm.assert_called_with("policy.can_view")

    def test_eligibility_request_all_good(self):
        with mock.patch("django.db.backends.utils.CursorWrapper") as mock_cursor:
            return_values = [
                list(range(1, 13)),
                [
                    core.datetime.date(2020, 1, 9),
                    core.datetime.date(2020, 1, 10),
                    20,
                    21,
                    True,
                    True,
                ],
            ][::-1]

            mock_cursor.return_value.__enter__.return_value.fetchone = (
                lambda: return_values.pop()
            )
            mock_user = mock.Mock(is_anonymous=False)
            mock_user.has_perm = mock.MagicMock(return_value=True)
            req = EligibilityRequest(chf_id="a")
            service = EligibilityService(mock_user)
            res = service.request(req)

            expected = EligibilityResponse(
                eligibility_request=req,
                prod_id=1,
                total_admissions_left=2,
                total_visits_left=3,
                total_consultations_left=4,
                total_surgeries_left=5,
                total_deliveries_left=6,
                total_antenatal_left=7,
                consultation_amount_left=8,
                surgery_amount_left=9,
                delivery_amount_left=10,
                hospitalization_amount_left=11,
                antenatal_amount_left=12,
                min_date_service=core.datetime.date(2020, 1, 9),
                min_date_item=core.datetime.date(2020, 1, 10),
                service_left=20,
                item_left=21,
                is_item_ok=True,
                is_service_ok=True,
            )
            self.assertEquals(expected, res)

    def test_eligibility_sp_call(self):
        mock_user = mock.Mock(is_anonymous=False)
        mock_user.has_perm = mock.MagicMock(return_value=True)
        req = EligibilityRequest(chf_id="070707070")
        service = EligibilityService(mock_user)
        res = service.request(req)
        expected = EligibilityResponse(
            eligibility_request=req,
            prod_id=4,
            total_admissions_left=0,
            total_visits_left=0,
            total_consultations_left=0,
            total_surgeries_left=0,
            total_deliveries_left=0,
            total_antenatal_left=0,
            consultation_amount_left=0.0,
            surgery_amount_left=0.0,
            delivery_amount_left=0.0,
            hospitalization_amount_left=0.0,
            antenatal_amount_left=0.0,
            min_date_service=None,
            min_date_item=None,
            service_left=0,
            item_left=0,
            is_item_ok=False,
            is_service_ok=False,
        )
        self.assertEquals(expected, res)


class RenewalsTestCase(TestCase):
    item_1 = None

    def setUp(self) -> None:
        self.i_user = InteractiveUser(
            login_name="test_batch_run", audit_user_id=978911, id=97891
        )
        self.user = User(i_user=self.i_user)

        self.item_1 = create_test_item("D")

    def tearDown(self) -> None:
        self.item_1.delete()

    def test_insert_renewals(self):
        # Given
        from core import datetime, datetimedelta

        insuree = create_test_insuree()
        product = create_test_product("VISIT")
        officer = create_test_officer()

        policy_not_expiring = create_test_policy(
            product=product,
            insuree=insuree,
            custom_props={"expiry_date": "2099-01-01", "officer": officer},
        )
        policy_expiring = create_test_policy(
            product=product,
            insuree=insuree,
            custom_props={
                "expiry_date": datetime.datetime.now() + datetimedelta(days=5),
                "officer": officer,
            },
        )

        # when
        insert_renewals(officer_id=officer.id)

        # then
        renewals = PolicyRenewal.objects.filter(insuree=insuree)
        expected_renewal = renewals.filter(policy=policy_expiring).first()
        self.assertIsNotNone(expected_renewal)

        should_not_renew = renewals.filter(policy=policy_not_expiring).first()
        self.assertIsNone(should_not_renew)

        # tearDown
        renewals.delete()
        policy_expiring.insuree_policies.all().delete()
        policy_expiring.delete()
        policy_not_expiring.insuree_policies.all().delete()
        policy_not_expiring.delete()
        officer.delete()
        product.delete()
        insuree.delete()

    def test_update_renewals(self):
        # Given
        from core import datetime, datetimedelta

        insuree = create_test_insuree()
        product = create_test_product("VISIT")
        officer = create_test_officer()

        policy_expiring = create_test_policy(
            product=product,
            insuree=insuree,
            custom_props={"expiry_date": "2019-01-01", "officer": officer},
        )
        policy_not_expired_yet = create_test_policy(
            product=product,
            insuree=insuree,
            custom_props={
                "expiry_date": datetime.datetime.now() + datetimedelta(days=5),
                "officer": officer,
            },
        )

        # when
        update_renewals()

        # then
        policy_expiring.refresh_from_db()
        policy_not_expired_yet.refresh_from_db()

        self.assertEquals(policy_expiring.status, Policy.STATUS_EXPIRED)
        self.assertEquals(policy_not_expired_yet.status, Policy.STATUS_ACTIVE)

        # tearDown
        policy_expiring.insuree_policies.all().delete()
        policy_expiring.delete()
        policy_not_expired_yet.insuree_policies.all().delete()
        policy_not_expired_yet.delete()
        officer.delete()
        product.delete()
        insuree.delete()

    def test_renewals_sms(self):
        # Given
        from core import datetime, datetimedelta

        insuree = create_test_insuree(
            custom_props={"chf_id": "TESTCHFSMS", "phone": "+33644444719"},
            family_custom_props={"location_id": 62},
        )
        product = create_test_product("VISIT")
        officer = create_test_officer(
            custom_props={"phone": "+32444444444", "phone_communication": True}
        )

        policy_expiring = create_test_policy(
            product=product,
            insuree=insuree,
            custom_props={"expiry_date": "2019-01-01", "officer": officer},
        )
        policy_not_expired_yet = create_test_policy(
            product=product,
            insuree=insuree,
            custom_props={
                "expiry_date": datetime.datetime.now() + datetimedelta(days=5),
                "officer": officer,
            },
        )

        family_template = "FAMSMS;{{renewal.insuree.chf_id}};{{renewal.insuree.last_name}};{{renewal.new_product.name}}"

        insert_renewals(officer_id=officer.id)

        # when
        sms_queue = policy_renewal_sms(family_template)

        # then
        policy_expiring.refresh_from_db()
        policy_not_expired_yet.refresh_from_db()

        self.assertTrue(len(sms_queue) > 0)
        insuree_sms = [sms for sms in sms_queue if sms.phone == "+33644444719"]
        self.assertEquals(len(insuree_sms), 1)
        self.assertEquals(
            insuree_sms[0].sms_message, "FAMSMS;TESTCHFSMS;Test Last;Test product VISIT"
        )

        officer_sms = [sms for sms in sms_queue if sms.phone == "+32444444444"]
        self.assertEquals(len(officer_sms), 1)
        self.assertIn("TESTCHFSMS", officer_sms[0].sms_message)
        self.assertIn("Agilo", officer_sms[0].sms_message)
        self.assertIn("Remorlogy", officer_sms[0].sms_message)
        self.assertIn("Jambero", officer_sms[0].sms_message)
        self.assertIn("Test product VISIT", officer_sms[0].sms_message)

        # tearDown
        officer.policy_renewals.all().delete()
        policy_expiring.insuree_policies.all().delete()
        policy_expiring.delete()
        policy_not_expired_yet.insuree_policies.all().delete()
        policy_not_expired_yet.delete()
        officer.delete()
        product.delete()
        insuree.delete()

    def test_insert_renewal_details(self):
        # Given
        from core import datetime, datetimedelta

        insuree_newpic = create_test_insuree(
            custom_props={"photo_date": datetime.datetime.now() - datetimedelta(days=30)})
        insuree_oldpic = create_test_insuree(custom_props={"photo_date": "2010-01-01", "chf_id": "CHFMARK"})  # 5 years by default
        product = create_test_product("VISIT")
        officer = create_test_officer(custom_props={"phone": "+32444444444", "phone_communication": True})
        photo_newpic = create_test_photo(insuree_newpic.id, officer.id)
        photo_oldpic = create_test_photo(insuree_oldpic.id, officer.id)

        policy_new_pic = create_test_policy(
            product=product,
            insuree=insuree_newpic,
            custom_props={
                "expiry_date": datetime.datetime.now() + datetimedelta(days=5),
                "officer": officer,
            },
        )
        policy_old_pic = create_test_policy(
            product=product,
            insuree=insuree_oldpic,
            custom_props={
                "expiry_date": datetime.datetime.now() + datetimedelta(days=5),
                "officer": officer,
            },
        )

        # when
        insert_renewals(officer_id=officer.id)

        # then
        renewals_new = PolicyRenewal.objects.filter(insuree=insuree_newpic)
        expected_renewal = renewals_new.filter(policy=policy_new_pic).first()
        self.assertIsNotNone(expected_renewal)
        self.assertIsNone(expected_renewal.details.first())

        renewals_old = PolicyRenewal.objects.filter(insuree=insuree_oldpic)
        expected_renewal_old = renewals_old.filter(policy=policy_old_pic).first()
        self.assertIsNotNone(expected_renewal_old)
        detail = expected_renewal_old.details.first()
        self.assertIsNotNone(detail)

        # ALSO WHEN
        sms_queue = policy_renewal_sms("UNUSED")  # Uses the default template
        self.assertEquals(len(sms_queue), 2)
        old_sms = [sms.sms_message for sms in sms_queue if "CHFMARK" in sms.sms_message]
        self.assertEquals(len(old_sms), 1)
        self.assertTrue('HOF\nCHFMARK\nTest Last First Second\n\n' in old_sms[0])

        # tearDown
        renewals_old.first().details.all().delete()
        renewals_old.delete()
        renewals_new.first().details.all().delete()
        renewals_new.delete()
        policy_old_pic.insuree_policies.all().delete()
        policy_old_pic.delete()
        policy_new_pic.insuree_policies.all().delete()
        policy_new_pic.delete()
        officer.delete()
        product.delete()
        photo_newpic.delete()
        photo_oldpic.delete()
        insuree_oldpic.delete()
        insuree_newpic.delete()
