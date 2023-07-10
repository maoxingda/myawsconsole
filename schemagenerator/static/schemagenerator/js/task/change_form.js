'use strict'
{
    // 扩展ajax请求参数
    function expand_ajax_params() {
        return '&db_conn_id=' + django.jQuery('#id_conn').val();
    }

    function update_status(that, status) {
        if (status === 'CREATED') {
            that.launch_show = true;
            that.launch_text = '启动';

            that.running_show = false;
            that.update_show = true;
        } else if (status === 'RUNNING') {
            that.launch_show = false;

            that.running_show = true;
            that.running_text = '运行中...';

            that.update_show = false;
            that.download_show = false;
        } else if (status === 'COMPLETED') {
            that.launch_show = true;
            that.launch_text = '重启';

            that.running_show = true;
            that.running_text = '已完成';

            that.download_show = true;
            that.update_show = true;
        } else {
            that.launch_show = true;
            that.launch_text = '重启';

            that.running_show = true;
            that.running_text = '失败';

            that.download_show = false;
            that.update_show = true;
        }
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
                    update_status(that, res.data.status);
                });
            },
            methods: {
                launch_task(url) {
                    const that = this;
                    update_status(that, 'RUNNING');
                    axios.get(url).then(function (res) {
                        if (res.data.code === 200) {
                            update_status(that, 'COMPLETED');
                            that.launch_show = false;
                        } else {
                            update_status(that, 'FAILED');
                        }
                    });
                },
                download_sql(url) {
                    axios.get(url).then(function (res) {
                        const data = res.data;
                        const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                        const filename = data.name + `-${now}.sql`;
                        downloadFile(filename, data.sql);
                    });
                },
                download_ods_ddl_sql(url) {
                    axios.get(url).then(function (res) {
                        const data = res.data;
                        const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                        const filename = data.schema + `-${now}.sql`;
                        downloadFile(filename, data.ddl_sql);
                    });
                },
                download_emr_ddl_sql(url) {
                    axios.get(url).then(function (res) {
                        const data = res.data;
                        const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                        const filename = data.schema + `-${now}.sql`;
                        downloadFile(filename, data.ddl_sql);
                    });
                }
            }
        }

        Vue.createApp(app_data).mount('#content-main');
    });
}
