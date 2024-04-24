odoo.define('portal_attendance_pro_adv.GeofenceRenderer', function (require) {
    'use strict';

    var BasicRenderer = require('web.BasicRenderer');
    var core = require('web.core');
    var qweb = core.qweb;

    const { loadJS } = require('@web/core/assets');

    var GeofenceRenderer = BasicRenderer.extend({
        template: 'GeofenceView',
        className: 'o_geofence_view',
        xmlDependencies: ['/portal_attendance_pro_adv/static/src/xml/geofence_template.xml'],
        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.olmap = null;
            this.state = state;
            this.drawingPath = params.drawingPath || 'shape_paths';
        },

        willStart: function () {
            var self = this;
            var def = this._rpc({
                route: '/portal_attendance_pro_adv/_get_gmap_api_key',
            }).then(function (data) {                
                self._gmp_api_key_prom = JSON.parse(data).gmap_api_key || '';                                
            });
            return Promise.all([this._super.apply(this, arguments), def]).then(async function(){
                var url = `https://maps.googleapis.com/maps/api/js?key=${self._gmp_api_key_prom}&libraries=drawing,places,geometry`;                
                await loadJS(url);
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments);
        },

        on_attach_callback: function () {
            var self = this;
            this._init_gmap();
            return this._super();
        },

        _init_gmap: function () {
            var gmap_div = this.$(".gmap_widget").get(0);
            $(gmap_div).css({
                width: '100%',
                height: '100%'
            });
            var map = this._load_gmap(gmap_div);
            if (this.gmap) {
                this._load_polygon_paths();
            }
        },
        _load_gmap: function(gmap_div){
            var self = this;
            if (!this.gmap) {
                self.gmap = new google.maps.Map(gmap_div, {
                    center: { lat: -33.8688, lng: 151.2195 },
                    mapTypeId: google.maps.MapTypeId.ROADMAP,                
                    fullscreenControl: true,
                    mapTypeControl: true,
                    gestureHandling: 'cooperative',
                    mapTypeControlOptions: {
                        mapTypeIds: ['satellite', 'hybrid', 'terrain'],
                        style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                    },
                    zoom: 12,
                    minZoom: 3,
                    maxZoom: 20,
                });
            }
            return self.gmap;
        },
        _load_polygon_paths: function () {
            var self = this;
            if (self.gmap){
                _.each(this.state.data, function (record) {
                    var value = record.data[self.drawingPath];
                    if (Object.keys(value).length > 0) {
                        var value = JSON.parse(value);
                        if (value.type === 'polygon') {
                            var polygon = self._drawPolygon(value.options);
                        }
                    }
                });
            }
        },
        _drawPolygon: function (options) {
            var self = this;
            var polygonOptions = {
                editable: false,
                map: this.gmap,
                strokeColor: '#FF0000',
                strokeOpacity: 0.86,
                strokeWeight: 1.1,
                fillColor: '#FF9999',
                fillOpacity: 0.34,
            }
            var polygon = new google.maps.Polygon(polygonOptions);
            polygon.setOptions(options);
            this._on_map_fitbounds(polygon.getPath());
            return polygon;
        },
        _on_map_fitbounds: function (paths, bounds) {
            var self = this;
            paths = paths || [];
            bounds = bounds || false;
            var latlngbounds = new google.maps.LatLngBounds();
            if (paths.length > 0) {
                for (var i = 0; i < paths.length; i++) {
                    latlngbounds.extend({
                        lat: paths.getAt(i).lat(), 
                        lng: paths.getAt(i).lng(),
                    });
                }
            } 
            else if (bounds) {
                latlngbounds.union(bounds);
            }
            self.gmap.fitBounds(latlngbounds);
            setTimeout(function () {
                self.gmap.setZoom(Math.min(self.gmap.getZoom(),12));
            });
        },
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments);
        },
    });

    return GeofenceRenderer;
});