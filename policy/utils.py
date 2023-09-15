from django.db.models import Func, DateTimeField


class MonthsAdd(Func):
    """
    Custom function to use the MS SQL Server DateAdd(MONTH, months, date)
    Usage: Foo.objects.annotate(end_date=MonthsAdd('duration', 'start_date')).filter(end_date__gt=datetime.now)
    """
    # https://stackoverflow.com/questions/33981468/using-dateadd-in-django-filter
    # suggested a trick to have it work with other databases. I think that it is actually feasible with F()
    # if we multiply a "1 month" interval by the amount of months. This doesn't work with SQL Server, hence this method
    # arg_joiner = " + CAST("
    # template = "%(expressions)s || ' months' as INTERVAL)"
    function = "DATEADD"
    template = '%(function)s(MONTH, %(expressions)s)'

    output_field = DateTimeField()
    arity = 2


def get_queryset_valid_at_date(queryset, date):
    filtered_qs = queryset.filter(
        validity_to__gte=date,
        validity_from__lte=date
    )
    if filtered_qs.exists():
        return filtered_qs
    return queryset.filter(validity_from__date__lte=date, validity_to__isnull=True)
