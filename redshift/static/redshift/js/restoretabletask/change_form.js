'use strict'
{
    function downloadFile(filename, content) {
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);
    }

    django.jQuery(function () {
        const btn_running = django.jQuery('#id_running');
        django.jQuery('#id_launch').click(function () {
            django.jQuery(this).toggle();
            btn_running.toggle();
            django.jQuery.get(django.jQuery(this).prop('href'), function () {
                btn_running.text('已完成...');
                django.jQuery('#id_download_sql').toggle();
            });
        });

        django.jQuery('#id_download_sql').click(function () {
            django.jQuery.get(django.jQuery(this).prop('href'), {}, function (data, status) {
                const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                const filename = data.name + `-${now}.sql`;
                downloadFile(filename, data.sql);
            });
        });
    });
}