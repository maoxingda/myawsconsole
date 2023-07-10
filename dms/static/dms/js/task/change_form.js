'use strict'
{
    django.jQuery(function () {
        const app_data = {
            data() {
                return {};
            },
            methods: {
                download_table_mappings(url) {
                    axios.get(url).then(function (res) {
                        const data = res.data;
                        const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                        const filename = data.name + `-${now}.json`;
                        downloadFile(filename, JSON.parse(data.table_mappings));
                    });
                }
            }
        }

        Vue.createApp(app_data).mount('#content-main');
    });
}
