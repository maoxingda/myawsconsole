'use strict'
{
    // 扩展ajax请求参数
    function expand_ajax_params() {
        return '&db_conn_id=' + django.jQuery('#id_conn').val();
    }

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
        // 监听select打开、关闭事件，为自动完成ajax请求提供更多上下文信息
        const auto_complete = django.jQuery('select.admin-autocomplete');
        auto_complete.on('select2:opening', function () {
            if (!history.orig_pathname) {
                history.orig_pathname = location.pathname;
            }
            this.modified_location_search_key = '?key=' + this.id;
            this.modified_location_search = this.modified_location_search_key + expand_ajax_params();
            history.replaceState(null, null, history.orig_pathname + this.modified_location_search);
        });
        auto_complete.on('select2:closing', function () {
            const keypart = (location.search + '&').split('&', 1)[0];
            if (keypart === this.modified_location_search_key) {
                history.replaceState(null, null, history.orig_pathname);
            }
        });

        const btn_launch = django.jQuery('#id_launch');
        const btn_running = django.jQuery('#id_running');
        django.jQuery('#id_launch').click(function () {
            btn_launch.toggle();
            if (btn_running.text() !== '失败') {
                btn_running.toggle();
            } else {
                btn_running.text('运行中...');
            }
            django.jQuery.get(django.jQuery(this).prop('href'), function (data, _) {
                if (data.code === 200) {
                    btn_running.text('已完成');
                    django.jQuery('#id_download_sql').toggle();
                } else {
                    btn_running.text('失败');
                    btn_launch.text('重启');
                    btn_launch.toggle();
                }
            });
        });

        django.jQuery('#id_download_sql').click(function () {
            django.jQuery.get(django.jQuery(this).prop('href'), {}, function (data, status) {
                const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                const filename = data.name + `-${now}.sql`;
                downloadFile(filename, data.sql);
            });
        });

        django.jQuery('#id_download_ods_ddl_sql').click(function () {
            django.jQuery.get(django.jQuery(this).prop('href'), {}, function (data, status) {
                const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                const filename = data.schema + `-${now}.sql`;
                downloadFile(filename, data.ddl_sql);
            });
        });

        django.jQuery('#id_download_emr_ddl_sql').click(function () {
            django.jQuery.get(django.jQuery(this).prop('href'), {}, function (data, status) {
                const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                const filename = data.schema + `-${now}.sql`;
                downloadFile(filename, data.ddl_sql);
            });
        });
    });
}