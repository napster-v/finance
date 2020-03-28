import json
from datetime import datetime

import pandas as pd
from pandas import DataFrame
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from finance.request_base import BaseViewSet, FilterMixin
from mf_tracker.models import AMC, Fund, Transaction, UserChosenFund
from mf_tracker.serializers import AMCSerializer, FundSerializer, TransactionSerializer, UserChosenFundSerializer


# Create your views here.

class TransactionViewSet(BaseViewSet, FilterMixin):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filterset_fields = ['fund__fund__amc__name', 'fund__fund__name']

    # @action(detail=False, methods=['get'])
    # def nav_graph(self, request):
    #     t = self.get_queryset()
    #     df: DataFrame = pd.DataFrame(t.values('fund__fund__name', 'nav', 'date'))
    #     # print(df)
    #     # df.set_index('date', inplace=True)
    #     df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    #     data = df.to_json(orient='records', index=True)
    #     grouped_df = df.groupby(df['date'].dt.year).min()
    #     print(grouped_df)
    #     return Response(json.loads(data), status=status.HTTP_200_OK)


class UserChosenFundViewSet(BaseViewSet):
    queryset = UserChosenFund.objects.all()
    serializer_class = UserChosenFundSerializer


class AMCViewSet(BaseViewSet):
    queryset = AMC.objects.all()
    serializer_class = AMCSerializer


class FundViewSet(BaseViewSet, FilterMixin):
    queryset = Fund.objects.all()
    serializer_class = FundSerializer
    filterset_fields = ['amc__name', ]
