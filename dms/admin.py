import json

from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.utils import unquote, flatten_fieldsets
from django.core.exceptions import PermissionDenied
from django.forms import all_valid
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from dms.models import Task, Endpoint
from dms.views import refresh_endpoints


class PermissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class TestAdmin(admin.ModelAdmin):
    def _changeform_view(self, request, object_id, form_url, extra_context):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        model = self.model
        opts = model._meta

        if request.method == "POST" and "_saveasnew" in request.POST:
            object_id = None

        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            if request.method == "POST":
                if not self.has_change_permission(request, obj):
                    raise PermissionDenied
            else:
                if not self.has_view_or_change_permission(request, obj):
                    raise PermissionDenied

            if obj is None:
                return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(
            request, obj, change=not add, fields=flatten_fieldsets(fieldsets)
        )
        # 修改部分
        original_form_validated = False
        # 修改部分 结束
        if request.method == "POST":
            form = ModelForm(request.POST, request.FILES, instance=obj)
            formsets, inline_instances = self._create_formsets(
                request,
                form.instance,
                change=not add,
            )
            form_validated = form.is_valid()
            # 修改部分
            original_form_validated = form_validated
            if form_validated:
                form_validated = False
            # 修改部分 结束
            if form_validated:
                new_object = self.save_form(request, form, change=not add)
            else:
                new_object = form.instance
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, not add)
                self.save_related(request, form, formsets, not add)
                change_message = self.construct_change_message(
                    request, form, formsets, add
                )
                if add:
                    self.log_addition(request, new_object, change_message)
                    return self.response_add(request, new_object)
                else:
                    self.log_change(request, new_object, change_message)
                    return self.response_change(request, new_object)
            else:
                form_validated = False
        else:
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(
                    request, form.instance, change=False
                )
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(
                    request, obj, change=True
                )

        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(fieldsets)
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        adminForm = helpers.AdminForm(
            form,
            list(fieldsets),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            self.get_prepopulated_fields(request, obj)
            if add or self.has_change_permission(request, obj)
            else {},
            readonly_fields,
            model_admin=self,
        )
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(
            request, formsets, inline_instances, obj
        )
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        if add:
            title = _("Add %s")
        elif self.has_change_permission(request, obj):
            title = _("Change %s")
        else:
            title = _("View %s")
        context = {
            **self.admin_site.each_context(request),
            "title": title % opts.verbose_name,
            "subtitle": str(obj) if obj else None,
            "adminform": adminForm,
            "object_id": object_id,
            "original": obj,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "media": media,
            "inline_admin_formsets": inline_formsets,
            "errors": helpers.AdminErrorList(form, formsets),
            "preserved_filters": self.get_preserved_filters(request),
        }

        # Hide the "Save" and "Save and continue" buttons if "Save as New" was
        # previously chosen to prevent the interface from getting confusing.
        if (
            request.method == "POST"
            and not form_validated
            and "_saveasnew" in request.POST
        ):
            context["show_save"] = False
            context["show_save_and_continue"] = False
            # Use the change template instead of the add template.
            add = False

        context.update(extra_context or {})

        # 修改部分
        if original_form_validated:
            return self.my_handler(request)
            # return refresh_endpoints(request)
        # 修改部分 结束

        return self.render_change_form(
            request, context, add=add, change=not add, obj=obj, form_url=form_url
        )

    def my_handler(self, request):
        pass


@admin.register(Task)
class TaskAdmin(PermissionAdmin):
    list_display = (
        'name',
        'html_actions',
    )
    fields = (
        'name',
        'format_table_mappings',
    )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        return mark_safe(' / '.join(buttons))

    @admin.display(description='表映射')
    def format_table_mappings(self, obj):
        return mark_safe(f'<pre>{json.dumps(json.loads(obj.table_mappings), indent=2)}</pre>')

    def changelist_view(self, request, extra_context=None):
        search_table = request.session.get('search_table')
        if not extra_context:
            extra_context = {}
        if search_table:
            extra_context['search_table'] = search_table
        return super().changelist_view(request, extra_context)


@admin.register(Endpoint)
class EndpointAdmin(PermissionAdmin, TestAdmin):
    def my_handler(self, request):
        return refresh_endpoints(request)

    def add_view(self, request, form_url="", extra_context=None):
        server_name = request.session.get('server_name')
        if not extra_context:
            extra_context = {}
        if server_name:
            extra_context['server_name'] = server_name
        return super().add_view(request, form_url, extra_context)

    list_display = (
        'identifier',
        'database',
        'html_actions',
    )
    exclude = ('identifier', 'arn', 'database', 'url', )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{reverse("dms:refresh_tasks")}?endpoint_id={obj.id}">DMS任务</a>',
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        return mark_safe(' / '.join(buttons))

    def changelist_view(self, request, extra_context=None):
        server_name = request.session.get('server_name')
        if not extra_context:
            extra_context = {}
        if server_name:
            extra_context['server_name'] = server_name
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request, obj=None):
        return True
