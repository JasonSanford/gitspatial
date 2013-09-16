$(document).ready(function () {
    $('.repo-sync').click(function (event) {
        event.preventDefault();
        var $this = $(this),
            synced = $this.hasClass('synced'),
            $tr= $this.parent().parent(),
            repo_id = $tr.data('repo-id'),
            $name_td = $tr.find('.repo-link-goes-here'),
            repo_name = $tr.data('repo-name'),
            repo_url = '/user/repo/' + repo_id;
        if ($this.hasClass('disabled')) {
            return;
        }
        if (synced) {
            $.ajax({
                url: $this.attr('href'),
                type: 'DELETE',
                success: function () {
                    visuallyUpdateRepoStatus(repo_id, 'not_synced');
                },
                error: function () {
                    alert('there was an error syncing');
                }
            });
        } else {
            visuallyUpdateRepoStatus(repo_id, 'syncing');
            $.ajax({
                url: $this.attr('href'),
                type: 'POST',
                dataType: 'json',
                success: function () {
                    pollRepoStatus(repo_id);
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

    function visuallyUpdateRepoStatus(repo_id, status) {
        var $tr = $('#repo-tr-' + repo_id),
            $td_repo_text_or_link = $tr.find('td.repo-link-goes-here'),
            $td_status = $tr.find('td.sync-status'),
            $a_repo_sync_button = $tr.find('a.repo-sync'),
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
                    default:
                        text = 'Not Synced';
                }
                return text;
            }()),
            text_or_link_content = (function () {
                var content,
                    name = $td_repo_text_or_link.data('name'),
                    url = $td_repo_text_or_link.data('url');
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
                        text = 'Unsync';
                        break;
                    default:
                        text = 'Unsync';
                }
                return text;
            }());
        $td_repo_text_or_link.html(text_or_link_content);
        $td_status.html(status_text);
        $a_repo_sync_button.text(button_text);
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
        } else if (status === 'error') {
            adds.push('btn-danger');
            removes.push('disabled', 'btn-success');
        }
        $a_repo_sync_button.removeClass(removes.join(' ')).addClass(adds.join(' '));
    }

    window.urs = visuallyUpdateRepoStatus;

    function pollRepoStatus(repo_id) {
        var interval = 3 * 1000,  // 3 seconds
            interval_name = 'polling_repo_' + repo_id;
        function getStatus() {
            $.ajax({
                url: '/user/repo/' + repo_id + '/sync_status',
                type: 'GET',
                dataType: 'json',
                success: function (data) {
                    if (data.status !== 'syncing') {
                        window.clearInterval(interval_name);
                        visuallyUpdateRepoStatus(repo_id, data.status);
                    }
                }
            });
        }
        interval_name = window.setInterval(function () {
            console.log('Getting status for ' + repo_id);
            getStatus();
        }, interval);
    }

});
