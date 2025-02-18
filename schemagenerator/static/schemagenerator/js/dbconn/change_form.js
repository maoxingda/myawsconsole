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

        const table_name_prefix = django.jQuery('#id_target_table_name_prefix');
        django.jQuery('#id_name').on('keyup', function () {
            table_name_prefix.val(`init_${django.jQuery(this).val()}_`);
        });

        django.jQuery('#id_password').attr('type', 'password');
    });
}
