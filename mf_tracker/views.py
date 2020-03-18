from django.shortcuts import render

from finance.request_base import BaseViewSet
from mf_tracker.models import Transaction, UserChosenFund
from mf_tracker.serializers import TransactionSerializer, UserChosenFundSerializer


# Create your views here.

class TransactionViewSet(BaseViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class UserChosenFundViewSet(BaseViewSet):
    queryset = UserChosenFund.objects.all()
    serializer_class = UserChosenFundSerializer
