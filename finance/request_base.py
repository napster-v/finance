from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from finance.utils import SuccessAPIRenderer

base_methods = ['HEAD', 'OPTIONS', 'TRACE']
read_only_social_fields = ['association', 'instagram_id', 'first_name', 'last_name', 'email', 'gender', 'birth_date',
                           'city', 'state']


class BaseViewSet(viewsets.ModelViewSet):
    queryset = None
    serializer_class = None
    renderer_classes = (SuccessAPIRenderer,)
    permission_classes = ()


class RequestBaseMixin:

    def get_serializer_class(self):
        raise NotImplementedError("Subclasses must override 'get_serializer_class'.")


class AuthenticationMixin:
    permission_classes = (IsAuthenticated,)


class AuthenticatedRequestBase(BaseViewSet, RequestBaseMixin, AuthenticationMixin):
    pass


class MultiSerializerViewSet(BaseViewSet):
    """
    Inherit this class, then define a dictionary of serializers WRT the action.
    Actions are 'list','create','retrieve','update','partial_update','destroy' for a DRF ModelViewSet
    """
    queryset = None
    serializer_class = {
        "default": None,
    }

    def get_serializer_class(self):
        return self.serializer_class.get(self.action, self.serializer_class.get("default"))


class AuthenticatedMultiSerializerViewSet(MultiSerializerViewSet, AuthenticationMixin):
    pass
