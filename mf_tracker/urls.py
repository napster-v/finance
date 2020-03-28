from rest_framework.routers import SimpleRouter

from mf_tracker.views import *

router = SimpleRouter()
router.register('transactions', TransactionViewSet, basename='transactions')
router.register('summary', UserChosenFundViewSet, basename='summary')
router.register('amc', AMCViewSet, basename='amc')
router.register('fund', FundViewSet, basename='fund')
urlpatterns = router.urls
