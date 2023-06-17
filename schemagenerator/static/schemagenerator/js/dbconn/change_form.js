'use strict'
{
    django.jQuery(function () {
        const db_type_mysql = django.jQuery('#id_db_type_0');
        const db_type_postgres = django.jQuery('#id_db_type_1');
        const radios = django.jQuery('input[type="radio"]')
        radios.change(function () {
            if (this.id === 'id_db_type_0') {
                django.jQuery('#id_port').val(3306);
            } else {
                django.jQuery('#id_port').val(5432);
            }
        });
    });
}