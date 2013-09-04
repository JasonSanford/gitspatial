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
        if (synced) {
            $.ajax({
                url: $this.attr('href'),
                type: 'DELETE',
                success: function () {
                    $this.removeClass('btn-danger synced').addClass('btn-success not-synced').text('Sync');
                    $name_td.html(repo_name);
                },
                error: function () {
                    alert('there was an error syncing');
                }
            });
        } else {
            $.ajax({
                url: $this.attr('href'),
                type: 'POST',
                success: function () {
                    $this.removeClass('btn-success not-synced').addClass('btn-danger synced').text('Unsync');
                    $name_td.html('<a href="' + repo_url + '">' + repo_name + '</a>');
                },
                error: function (jqXHR) {
                    response = JSON.parse(jqXHR.responseText);
                    if ('message' in response) {
                        alert(response.message);
                    }
                },
                complete: function (jqXHR, status) {
                    console.log(jqXHR);
                    console.log(status);
                }
            });
        }
    });
});
