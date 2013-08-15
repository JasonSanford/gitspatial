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
        if (synced) {
            $.ajax({
                url: $this.attr('href'),
                type: 'DELETE',
                success: function () {
                    $this.removeClass('btn-danger synced').addClass('btn-success not-synced').text('Sync');
                    $name_td.html(fs_name);
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
                    $name_td.html('<a href="' + fs_url + '">' + fs_name + '</a>');
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

    $('.tr-fs').hover(function () {
        $(this).find('.icon-pencil').css({'background-position': '0 -72px'});
    }, function () {
        $(this).find('.icon-pencil').css({'background-position': '0 -2000px'});
    });

    $('.pencil.edit').click(function (event) {
        event.stopPropagation();
        event.preventDefault();
        $(this).siblings('.editable').editable('toggle');
    });
});
