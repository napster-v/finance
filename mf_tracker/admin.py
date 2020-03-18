from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from mf_tracker.models import AMC, Cap, Fund, Transaction, UserChosenFund

# Register your models here.

app_models = apps.get_app_config('mf_tracker').get_models()


# class TransactionAdmin(admin.TabularInline):
#     model = Transaction
#     extra = 2
#
#
# @admin.register(UserChosenFund)
# class UserSelectedFundAdmin(admin.ModelAdmin):
#     inlines = [TransactionAdmin, ]
#
#
# for model in app_models:
#     try:
#         admin.site.register(model)
#     except AlreadyRegistered:
#         pass
#
#
# @admin.register(AMC)
class AMCResource(resources.ModelResource):
    class Meta:
        model = AMC


class CapResource(resources.ModelResource):
    class Meta:
        model = Cap


class FundResource(resources.ModelResource):
    class Meta:
        model = Fund


class UserChosenFundResource(resources.ModelResource):
    class Meta:
        model = UserChosenFund
        exclude = ('created', 'modified', 'deleted')
        use_transactions = True
        clean_model_instances = True

    def get_queryset(self):
        return super().get_queryset()


class TransactionInline(admin.TabularInline):
    model = Transaction


class TransactionResource(resources.ModelResource):
    class Meta:
        model = Transaction
        exclude = ('created', 'modified', 'deleted')
        use_transactions = True
        clean_model_instances = True


@admin.register(Transaction)
class TransactionAdmin(ImportExportModelAdmin):
    resource_class = TransactionResource
    list_display = ['fund', 'nav', 'date', 'amount', 'mode', ]
    list_editable = ['mode', ]
    search_fields = ['fund__fund__amc__name']


@admin.register(UserChosenFund)
class UserChosenFundAdmin(ImportExportModelAdmin):
    resource_class = UserChosenFundResource
    inlines = [TransactionInline, ]
    list_display = ['id', 'fund', 'amount', 'active']


@admin.register(Fund)
class FundAdmin(ImportExportModelAdmin):
    resource_class = FundResource


@admin.register(AMC)
class AMCAdmin(ImportExportModelAdmin):
    resource_class = AMCResource


@admin.register(Cap)
class CapAdmin(ImportExportModelAdmin):
    resource_class = CapResource

# admin.site.register(AMC, AMCAdmin)
