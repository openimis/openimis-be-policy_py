from django.test import TestCase
from django.core.exceptions import PermissionDenied
from unittest import mock
import xml.etree.ElementTree as ET
from .services import *
import core
import json


class EligibilityServiceTestCase(TestCase):

    def test_eligibility_request_permission_denied(self):
        with mock.patch("django.db.backends.utils.CursorWrapper") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.description = None
            mock_user = mock.Mock(is_anonymous=False)
            mock_user.has_perm = mock.MagicMock(return_value=False)
            req = EligibilityRequest(chf_id='a')
            service = EligibilityService(mock_user)
            with self.assertRaises(PermissionDenied) as cm:
                service.request(req)
            mock_user.has_perm.assert_called_with('policy.can_view')

    def test_eligibility_request_all_good(self):
        with mock.patch("django.db.backends.utils.CursorWrapper") as mock_cursor:
            return_values = [
                list(range(1, 13)),
                [core.datetime.date(2020, 1, 9),
                 core.datetime.date(2020, 1, 10),
                 20, 21, True, True]
            ][::-1]

            mock_cursor.return_value.__enter__.return_value.fetchone = lambda: return_values.pop()
            mock_user = mock.Mock(is_anonymous=False)
            mock_user.has_perm = mock.MagicMock(return_value=True)
            req = EligibilityRequest(chf_id='a')
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
                is_service_ok=True
            )
            self.assertEquals(expected, res)

    def test_eligibility_sp_call(self):
        mock_user = mock.Mock(is_anonymous=False)
        mock_user.has_perm = mock.MagicMock(return_value=True)
        req = EligibilityRequest(chf_id='070707070')
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
            is_service_ok=False
        )
        self.assertEquals(expected, res)
