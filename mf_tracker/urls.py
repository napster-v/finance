from rest_framework.routers import SimpleRouter

from mf_tracker.views import TransactionViewSet, UserChosenFundViewSet

router = SimpleRouter()
router.register('transactions', TransactionViewSet, basename='transactions')
router.register('ucf', UserChosenFundViewSet, basename='ucf')
urlpatterns = router.urls
