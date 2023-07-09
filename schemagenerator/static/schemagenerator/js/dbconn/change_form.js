'use strict'
{
    django.jQuery(function () {
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
