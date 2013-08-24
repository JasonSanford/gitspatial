$.fn.editable.defaults.ajaxOptions = {type: 'PUT'};

$('#pencil').click(function(e) {
    e.stopPropagation();
    e.preventDefault();
    $('#name').editable('toggle');
});

(function() {
    var start_location = new L.LatLng(gs.fs.center.lat, gs.fs.center.lng),
        road_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-qh86l7s4/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        satellite_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-c487ey3y/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        map = new L.Map('map-container', {
            center: start_location,
            zoom: 18,
            layers: [
                road_layer
            ]
        }),
        feature_set_layer = new L.GeoJSON(gs.features, {
            onEachFeature: function (feature, layer) {
                layer.on('mouseover', function () {
                    highlightTR(feature.id);
                });
                layer.on('mouseout', function () {
                    unhighlightTR(feature.id);
                });
            }
        });
    map
        .addLayer(feature_set_layer)
        .fitBounds([[gs.fs.bounds[1], gs.fs.bounds[0]], [gs.fs.bounds[3], gs.fs.bounds[2]]]);
    L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, null).addTo(map);

    $('.feature').on('mouseover', function () {
        var $this = $(this),
            id = $this.data('feature-id');
        highlightTR(id);
    });

    $('.feature').on('mouseout', function () {
        var $this = $(this),
            id = $this.data('feature-id');
        unhighlightTR(id);
    });

    function highlightTR(id) {
        $('#tr-' + id).addClass('info');
        highlightFeature(id);
    }

    function unhighlightTR(id) {
        $('#tr-' + id).removeClass('info');
        unhighlightFeature(id);
    }

    function highlightFeature(id) {
        feature_set_layer.eachLayer(function (layer) {
            if (id == layer.feature.id) {
                if (layer instanceof L.Marker) {
                    var highlight_icon = L.icon({
                        iconUrl: '/static/img/markers/marker-icon-hover.png'
                    });
                    if (layer instanceof L.Marker) {
                        layer.setIcon(highlight_icon);
                    }
                } else {
                    layer.setStyle({opacity: 1});
                }
            }
        });
    }

    function unhighlightFeature(id) {
        feature_set_layer.eachLayer(function (layer) {
            if (id == layer.feature.id) {
                if (layer instanceof L.Marker) {
                    var default_icon = new L.Icon.Default();
                    if (layer instanceof L.Marker) {
                        layer.setIcon(default_icon);
                    }
                } else {
                    layer.setStyle({opacity: 0.5});
                }
            }
        });
    }
}());