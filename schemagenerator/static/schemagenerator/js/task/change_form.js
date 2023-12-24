'use strict'
{
    // 扩展ajax请求参数
    function expand_ajax_params() {
        return '&db_conn_id=' + django.jQuery('#id_conn').val();
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

        const id_download_sql         = django.jQuery('#id_download_sql');
        const id_download_emr_ddl_sql = django.jQuery('#id_download_emr_ddl_sql');

        const date_format = 'YYYY[_]MM[_]DD[T]HH[_]mm[_]ss';

        // 下载查询SQL
        id_download_sql.click(function (e) {
            e.preventDefault();
            axios.get(this.href).then(function (res) {
                const data = res.data;
                const now = dayjs().format(date_format);
                const filename = data.name + `-${now}.sql`;
                downloadFile(filename, data.sql);
            });
        });

        // 下载emr建表DDL
        id_download_emr_ddl_sql.click(function (e) {
            e.preventDefault();
            axios.get(this.href).then(function (res) {
                const data = res.data;
                const now = dayjs().format(date_format);
                const filename = `ddl-${now}.sql`;
                downloadFile(filename, data.ddl_sql);
            });
        });
    });
}
