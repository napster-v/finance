from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView

from auth_base.views import *

router = SimpleRouter()
router.register('user', UserViewSet)
router.register('login/facebook', FacebookSocialLoginViewSet, basename='fb_login')
router.register('login/google', GoogleSocialLoginViewSet, basename='g_login')
router.register('login/twitter', TwitterSocialLoginViewSet, basename='t_login')
url = [
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
urlpatterns = router.urls + url
