'use strict'
{
    django.jQuery(function () {
        const btn_launch = django.jQuery('#id_launch');
        const btn_running = django.jQuery('#id_running');
        django.jQuery('#id_launch').click(function () {
            btn_launch.toggle();
            if (btn_running.text() !== '失败') {
                btn_running.toggle();
            } else {
                btn_running.text('运行中...');
            }
            axios.get(btn_launch.prop('href')).then(function () {
                btn_running.text('已完成...');
                django.jQuery('#id_download_sql').toggle();
            }, function () {
                btn_launch.text('重启');
                btn_launch.toggle();
                btn_running.text('失败');
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
