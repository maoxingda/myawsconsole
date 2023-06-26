'use strict'
{
    django.jQuery(function () {
        const btn_running = django.jQuery('#id_running');
        django.jQuery('#id_launch').click(function () {
            django.jQuery(this).toggle();
            btn_running.toggle();
            django.jQuery.get(django.jQuery(this).prop('href'), function () {
                btn_running.text('已完成...');
            });
        });
    });
}