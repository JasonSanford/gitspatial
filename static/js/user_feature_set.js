$.fn.editable.defaults.ajaxOptions = {type: 'PUT'};

$('#pencil').click(function(e) {
    e.stopPropagation();
    e.preventDefault();
    $('#name').editable('toggle');
});