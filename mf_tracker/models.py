from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import models

from auth_base.models import AppUser
from finance.base_model import AppBaseModel, CHAR_FIELD_MAX_LENGTH


# Create your models here.

class NameField(models.Model):
    name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Cap(AppBaseModel, NameField):
    pass


class AMC(AppBaseModel, NameField):
    pass


class Fund(AppBaseModel, NameField):
    cap = models.ForeignKey(Cap, on_delete=models.CASCADE)
    amc = models.ForeignKey(AMC, on_delete=models.CASCADE)
    scheme_code = models.IntegerField()


class UserChosenFund(AppBaseModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    duration = models.PositiveSmallIntegerField(help_text="Goal in months")
    amount = models.PositiveIntegerField(verbose_name="Monthly SIP Amount")
    sip_date = models.DateField(blank=True, null=True)
    purchase_date = models.DateField()
    maturity_date = models.DateField(blank=True)
    folio_no = models.PositiveIntegerField(blank=True, null=True)
    active = models.BooleanField(default=True, help_text="Are you still investing?")

    def clean(self):
        if not self.maturity_date:
            self.maturity_date = self.purchase_date + relativedelta(months=self.duration)

    @property
    def fund_name(self):
        return self.fund.name

    @property
    def fund_cap(self):
        return self.fund.cap.name

    @property
    def amc(self):
        return self.fund.amc.name


class Transaction(AppBaseModel):
    class Mode(models.IntegerChoices):
        sip = 1, 'SIP'
        additional = 2, 'ADDITIONAL/OTI'

    fund = models.ForeignKey(UserChosenFund, on_delete=models.CASCADE)
    mode = models.IntegerField(choices=Mode.choices, default=1)
    amount = models.PositiveIntegerField()
    nav = models.DecimalField(decimal_places=3, max_digits=8)
    units = models.DecimalField(decimal_places=3, max_digits=8, blank=True)
    date = models.DateField()

    class Meta:
        ordering = ['id', ]

    def clean(self):
        if not self.amount:
            self.amount = self.fund.amount

        if not self.units:
            self.units = Decimal(self.amount / self.nav)

    @property
    def fund_name(self):
        return self.fund.fund.name

    @property
    def fund_cap(self):
        return self.fund.fund.cap.name

    @property
    def amc(self):
        return self.fund.fund.amc.name

# class Reinvestment(AppBaseModel):
#     from_ = models.ForeignKey(UserChosenFund, on_delete=models.CASCADE)
#     to = models.ForeignKey(UserChosenFund, on_delete=models.CASCADE)
