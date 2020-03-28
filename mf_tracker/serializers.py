from django.db.models import Avg, Sum
from rest_framework import serializers

from finance.serializers import AppBaseSerializer
from mf_tracker.models import AMC, Fund, Transaction, UserChosenFund


class TransactionSerializer(AppBaseSerializer):
    fund = serializers.SerializerMethodField()
    # cap = serializers.SerializerMethodField()
    amc = serializers.SerializerMethodField()

    # cmv = serializers.SerializerMethodField()

    # duration = serializers.SerializerMethodField()
    # completed = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        exclude = ['mode', 'id']

    @staticmethod
    def get_fund(obj: Transaction):
        return obj.fund_name

    @staticmethod
    def get_cap(obj: Transaction):
        return obj.fund_cap

    @staticmethod
    def get_amc(obj: Transaction):
        return obj.amc

    @staticmethod
    def get_cmv(obj: Transaction):
        latest_nav = UserChosenFundSerializer.get_latest_nav(obj)
        return round(latest_nav * float(obj.units), 2)


class UserChosenFundSerializer(AppBaseSerializer):
    fund = serializers.SerializerMethodField()
    cap = serializers.SerializerMethodField()
    amc = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    amount_invested = serializers.SerializerMethodField()
    total_units = serializers.SerializerMethodField()
    average_nav = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    gain_loss = serializers.SerializerMethodField()
    cagr = serializers.SerializerMethodField()
    latest_nav = serializers.SerializerMethodField()

    class Meta:
        model = UserChosenFund
        exclude = ['user', 'id']

    @staticmethod
    def get_fund(obj: Transaction):
        return obj.fund_name

    @staticmethod
    def get_cap(obj: Transaction):
        return obj.fund_cap

    @staticmethod
    def get_amc(obj: Transaction):
        return obj.amc

    @staticmethod
    def get_completed(obj: UserChosenFund):
        return obj.transaction_set.filter(mode=1).count()

    @staticmethod
    def get_amount_invested(obj: UserChosenFund):
        q = obj.transaction_set.aggregate(Sum('amount'))
        return q.get('amount__sum')

    @staticmethod
    def get_total_units(obj: UserChosenFund):
        q = obj.transaction_set.aggregate(Sum('units'))
        return float(q.get('units__sum'))

    @staticmethod
    def get_average_nav(obj: UserChosenFund):
        q = obj.transaction_set.aggregate(Avg('nav'))
        return round(float(q.get('nav__avg')), 2)

    def get_current_value(self, obj: UserChosenFund):
        return round(self.get_total_units(obj) * self.get_latest_nav(obj), 3)

    def get_gain_loss(self, obj):
        return round(self.get_current_value(obj) - self.get_amount_invested(obj), 3)

    def get_cagr(self, obj):
        result = float(self.get_current_value(obj) / self.get_amount_invested(obj)) ** (
                1 / (self.get_completed(obj) / 12)) - 1
        return round(result, 2)

    @staticmethod
    def get_latest_nav(obj):
        # import requests
        # url = "https://latest-mutual-fund-nav.p.rapidapi.com/fetchLatestNAV"
        # scheme_code = None
        # if isinstance(obj, UserChosenFund):
        #     scheme_code = obj.fund.scheme_code
        # elif isinstance(obj, Transaction):
        #     scheme_code = obj.fund.fund.scheme_code
        # querystring = {"SchemeType": "All", "SchemeCode": f'{scheme_code}'}
        # headers = {
        #     'x-rapidapi-host': "latest-mutual-fund-nav.p.rapidapi.com",
        #     'x-rapidapi-key': "557074dc3dmsh01d5a278784ffd8p10ae33jsnbb1d38fad4f9"
        # }
        # response = requests.get(url, headers=headers, params=querystring)
        #
        # return float(response.json()[0].get("Net Asset Value"))
        return 25


class AMCSerializer(AppBaseSerializer):
    class Meta:
        model = AMC


class FundSerializer(AppBaseSerializer):
    class Meta:
        model = Fund
