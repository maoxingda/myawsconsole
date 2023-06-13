'use strict'
{
    django.jQuery(function () {
        django.jQuery('#id_launch').click(function () {
            django.jQuery(this).toggle();
            django.jQuery('#id_running').toggle();
            django.jQuery.get(django.jQuery(this).prop('href'), function () {
                django.jQuery('#id_launch').toggle();
                django.jQuery('#id_running').toggle();
            });
        });
    });
}