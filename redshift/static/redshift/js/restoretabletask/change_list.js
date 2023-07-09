'use strict'
{
    django.jQuery(function () {
        django.jQuery('#id_batch_download_sql').click(function () {
            let url = '{% url "redshift:batch_download_sql" %}?task_ids='
            django.jQuery('input[type="checkbox"][name="_selected_action"]').each(function (i, e) {
                if (django.jQuery(e).prop('checked')) {
                    url += django.jQuery(e).val() + ',';
                }
            });
            django.jQuery.get(url, {}, function (data, status) {
                const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                const filename = data.name + `-${now}.sql`;
                downloadFile(filename, data.sqls);
            });
        });
    });
}
