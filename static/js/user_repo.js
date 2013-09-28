$(document).ready(function () {
    $('.fs-sync').click(function (event) {
        event.preventDefault();
        var $this = $(this),
            synced = $this.hasClass('synced'),
            $tr= $this.parent().parent(),
            fs_id = $tr.data('fs-id'),
            $name_td = $tr.find('.fs-link-goes-here'),
            fs_name = $tr.data('fs-name'),
            fs_url = '/user/feature_set/' + fs_id;
        if ($this.hasClass('disabled')) {
            return;
        }
        if (synced) {
            $.ajax({
                url: $this.attr('href'),
                type: 'DELETE',
                success: function () {
                    visuallyUpdateFeatureSetStatus(fs_id, 'not_synced');
                },
                error: function () {
                    alert('there was an error syncing');
                }
            });
        } else {
            visuallyUpdateFeatureSetStatus(fs_id, 'syncing');
            $.ajax({
                url: $this.attr('href'),
                type: 'POST',
                success: function () {
                    pollFeatureSetStatus(fs_id);
                },
                error: function (jqXHR) {
                    response = JSON.parse(jqXHR.responseText);
                    if ('message' in response) {
                        alert(response.message);
                    }
                }
            });
        }
    });

    function visuallyUpdateFeatureSetStatus(fs_id, status) {
        var $tr = $('#fs-tr-' + fs_id),
            $td_fs_text_or_link = $tr.find('td.fs-link-goes-here'),
            $td_status = $tr.find('td.sync-status'),
            $a_fs_sync_button = $tr.find('a.fs-sync'),
            status_text = (function () {
                var text;
                switch (status) {
                    case 'syncing':
                        text = 'Syncing';
                        break;
                    case 'synced':
                        text = 'Synced';
                        break;
                    case 'not_synced':
                        text = 'Not Synced';
                        break;
                    case 'error':
                        text = 'Error Syncing';
                        break;
                    case 'memory_error':
                        text = 'GeoJSON Too Large';
                        break;
                    case 'invalid_geojson_error':
                        text = 'Invalid GeoJSON';
                        break;
                    default:
                        text = 'Not Synced';
                }
                return text;
            }()),
            text_or_link_content = (function () {
                var content,
                    name = $td_fs_text_or_link.data('fs-name'),
                    url = $td_fs_text_or_link.data('fs-url');
                if (status === 'synced') {
                    content = '<a href="' + url + '">' + name + '</a>';
                } else {
                    content = name;
                }
                return content;
            }()),
            button_text = (function () {
                var text;
                switch (status) {
                    case 'syncing':
                        text = 'Syncing';
                        break;
                    case 'synced':
                        text = 'Unsync';
                        break;
                    case 'not_synced':
                        text = 'Sync';
                        break;
                    case 'error':
                    case 'memory_error':
                    case 'invalid_geojson_error':
                        text = 'Unsync';
                        break;
                    default:
                        text = 'Unsync';
                }
                return text;
            }());
        $td_fs_text_or_link.html(text_or_link_content);
        $td_status.html(status_text);
        $a_fs_sync_button.text(button_text);
        var adds = [],
            removes = [];
        if (status === 'syncing') {
            adds.push('disabled');
            removes.push('btn-success', 'not_synced');
        } else if (status === 'synced') {
            adds.push('btn-danger', 'synced');
            removes.push('disabled', 'btn-success');
        } else if (status === 'not_synced') {
            adds.push('btn-success');
            removes.push('disabled', 'btn-danger', 'synced');
        } else if (['error', 'memory_error', 'invalid_geojson_error'].indexOf(status) > -1) {
            adds.push('btn-danger');
            removes.push('disabled', 'btn-success');
        }
        $a_fs_sync_button.removeClass(removes.join(' ')).addClass(adds.join(' '));
    }

    function pollFeatureSetStatus(fs_id) {
        var interval = 3 * 1000;  // 3 seconds
        function getStatus() {
            $.ajax({
                url: '/user/feature_set/' + fs_id + '/sync_status',
                type: 'GET',
                dataType: 'json',
                success: function (data) {
                    if (data.status !== 'syncing') {
                        window.clearInterval(interval_name);
                        visuallyUpdateFeatureSetStatus(fs_id, data.status);
                    }
                }
            });
        }
        interval_name = window.setInterval(function () {
            console.log('Getting status for ' + fs_id);
            getStatus();
        }, interval);
    }
});
