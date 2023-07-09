'use strict'
{
    django.jQuery(function () {
        django.jQuery('#id_download_table_mappings').click(function () {
            axios.get(django.jQuery(this).prop('href')).then(function (res) {
                const data = res.data;
                const now = dayjs().format('YYYY[_]MM[_]DD[T]HH[_]mm[_]ss');
                const filename = data.name + `-${now}.json`;
                downloadFile(filename, JSON.parse(data.table_mappings));
            });
        });
    });
}
