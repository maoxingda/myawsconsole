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

        const app_data = {
            data() {
                return {
                    launch_text: null,
                    running_text: null,

                    launch_show: null,
                    running_show: null,
                    download_show: null,
                    update_show: null
                }
            },
            created() {
                const that = this;
                axios.get(location.pathname.split('/').slice(0, 4).join('/') + '/').then(function (res) {
                    that.task = res.data;
                    if (that.task.status === 'CREATED') {
                        that.launch_show = true;
                        that.launch_text = '启动';

                        that.running_show = false;
                    } else if (that.task.status === 'RUNNING') {
                        that.running_show = true;
                        that.running_text = '运行中...';

                        that.update_show = false;
                    } else if (that.task.status === 'COMPLETED') {
                        that.launch_show = true;
                        that.launch_text = '重启';

                        that.running_show = true;
                        that.running_text = '已完成';

                        that.download_show = true;
                    }
                });
            },
            methods: {
                launch_task(url) {
                    const that = this;
                    that.launch_show = false;
                    that.download_show = false;
                    that.update_show = false;
                    that.running_show = true;
                    that.running_text = '运行中...';
                    axios.get(url).then(function (res) {
                        const data = res.data;
                        if (data.code === 200) {
                            that.running_text = '已完成';
                            that.download_show = true
                        } else {
                            that.running_text = '失败';

                            that.launch_show = true;
                            that.launch_text = '重启';
                        }
                    });
                }
            }
        }

        Vue.createApp(app_data).mount('#content-main');
    });
}
