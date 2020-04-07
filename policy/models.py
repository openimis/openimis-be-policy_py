import uuid

from django.conf import settings
from django.db import models
from core import fields
from core.models import Officer
from graphql import ResolveInfo
from insuree.models import Family
from location.models import UserDistrict
from product.models import Product
from core import models as core_models


class Policy(core_models.VersionedModel):
    id = models.AutoField(db_column='PolicyID', primary_key=True)
    uuid = models.CharField(db_column='PolicyUUID', max_length=36, default=uuid.uuid4, unique = True)

    stage = models.CharField(db_column='PolicyStage', max_length=1, blank=True, null=True)
    status = models.SmallIntegerField(db_column='PolicyStatus', blank=True, null=True)
    value = models.DecimalField(db_column='PolicyValue', max_digits=18, decimal_places=2, blank=True, null=True)

    family = models.ForeignKey(Family, models.DO_NOTHING, db_column='FamilyID')
    enroll_date = fields.DateField(db_column='EnrollDate')
    start_date = fields.DateField(db_column='StartDate')
    effective_date = fields.DateField(db_column='EffectiveDate', blank=True, null=True)
    expiry_date = fields.DateField(db_column='ExpiryDate', blank=True, null=True)

    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='ProdID', related_name="policies")
    officer = models.ForeignKey(Officer, models.DO_NOTHING, db_column='OfficerID', blank=True, null=True, related_name="policies")

    offline = models.BooleanField(db_column='isOffline', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # row_id = models.BinaryField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblPolicy'

    STATUS_IDLE = 1
    STATUS_ACTIVE = 2
    STATUS_SUSPENDED = 4
    STATUS_EXPIRED = 8

    STAGE_NEW = 'N'
    STAGE_RENEWED = 'R'

    @classmethod
    def get_queryset(cls, queryset, user):
        queryset = Policy.filter_queryset(queryset)
        # GraphQL calls with an info object while Rest calls with the user itself
        if isinstance(user, ResolveInfo):
            user = user.context.user
        if settings.ROW_SECURITY and user.is_anonymous:
            return queryset.filter(id=-1)
        # TODO: check the access to the policy information but how ?
        #   Policy -> Product -> Location ? Policy -> Insurees -> HF -> Location ?
        # if settings.ROW_SECURITY:
        #     dist = UserDistrict.get_user_districts(user._u)
        #     return queryset.filter(
        #         health_facility__location_id__in=[l.location.id for l in dist]
        #     )
        return queryset
