'use strict'
{
    django.jQuery(function () {
        const btn_running = django.jQuery('#id_running');
        const status = django.jQuery('#restoreclustertask_form > div > fieldset > div.form-row.field-status > div > div');
        django.jQuery('#id_launch').click(function () {
            django.jQuery(this).toggle();
            btn_running.toggle();
            status.text('RUNNING');
            django.jQuery.get(django.jQuery(this).prop('href'), function () {
                btn_running.text('已完成...');
                status.text('COMPLETED');
            });
        });
    });
}