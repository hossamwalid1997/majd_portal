/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { loadJS } from "@web/core/assets";

var core = require('web.core');
var _t = core._t;
var qweb = core.qweb;

const { Component, onPatched, onWillStart, onWillUnmount, onWillUpdateProps, useEffect, useRef} = owl;

export class GeofenceDrawing extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.mapContainerRef = useRef("mapContainer");

        this.selectedPolygons = {};
        this.colorEditMode = '#FF0000';
        this.selectedPolygon = null;

        if (!this.props.value) {
            this.props.value = 'Empty';
        }

        useEffect(
            () => {
                if (typeof google === 'object' && typeof google.maps === 'object') {
                    this.gmap = new google.maps.Map(this.mapContainerRef.el, {
                        center: { lat: -33.8688, lng: 151.2195 },
                        mapTypeId: google.maps.MapTypeId.ROADMAP,                
                        fullscreenControl: true,
                        mapTypeControl: true,
                        gestureHandling: 'cooperative',
                        mapTypeControlOptions: {
                            mapTypeIds: ['satellite', 'hybrid', 'terrain'],
                            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                        },
                        zoom: 3,
                        minZoom: 3,
                        maxZoom: 20,
                    });
                    if(this.gmap){
                        this.loadPolygonPaths();
                    }
                }else{
                    this.notification.add(
                        this.env._t('Google Map API is not loaded.')
                    );
                    return;
                }
            },
            () => []
        );
        useEffect(() => {
            this.updateMap();
        });

        onWillStart(this.onWillStart);
        onPatched(this.onPatched);
    }

    async onWillStart() {
        var self = this;
        const key = await this._getGmapAPIKey();
        if (key){
            await loadJS(`https://maps.googleapis.com/maps/api/js?key=${key}&libraries=drawing,places,geometry`);
        }
        else{
            this.notification.add(
                this.env._t('The google map API key is not set up!')
            );
            return;
        }
    }

    onPatched(){

    }

    async _getGmapAPIKey() {
        if (!this._gmp_api_key_prom) {
            this._gmp_api_key_prom = new Promise(async resolve => {
                const data = await this.rpc('/portal_attendance_geo/_get_gmap_api_key');
                resolve(JSON.parse(data).gmap_api_key || '');
            });
        }
        return this._gmp_api_key_prom;
    }

    updateMap() {
        if (this.gmap) {
            this.initDrawingManager();
            this.loadSearchControls();
        }
    }

    initDrawingManager(){
        if (!this.drawing_manager){
            this.drawing_manager = new google.maps.drawing.DrawingManager({
                drawingControl: true,
                drawingControlOptions: {
                    position: google.maps.ControlPosition.LEFT_CENTER,
                    drawingModes: ['polygon']
                },
                map: this.gmap,
                
                polygonOptions: {
                    fillColor: this.colorEditMode,
                    strokeWeight: 0,
                    fillOpacity: 0.45,
                    editable: true
                },
            });
            this.drawing_manager.setMap(this.gmap);
            google.maps.event.addListener(this.drawing_manager, 'overlaycomplete', this.overlayCompleted.bind(this));
            google.maps.event.addListener(this.drawing_manager, 'drawingmode_changed', this.clearSelectedShape.bind(this));
            google.maps.event.addListener(this.gmap, 'click', this.clearSelectedShape.bind(this));
            this.loadDeleteControls();
        }
    }

    loadDeleteControls(){
        if (this.$delete_buttton === undefined) {
            this.$delete_buttton = $(qweb.render('GmapDeleteButton', {
                widget: this
            }));
            this.gmap.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(this.$delete_buttton.get(0));
            this.$delete_buttton.on('click', this.deleteSelectedShape.bind(this));
        }
    }

    loadPolygonPaths () {
        var value = JSON.parse(JSON.stringify(this.props.value));
        if (value && value != 'Empty') {
            value = JSON.parse(value);
            if (value.type === 'polygon') {
                var polygon = this.drawPolygon(value.options);
                polygon.setOptions({
                    strokeColor: this.colorEditMode,
                    fillColor: this.colorEditMode,
                });
                var newPolygon = polygon;
                newPolygon.type = 'polygon';
                google.maps.event.addListener(newPolygon, 'dblclick', this.setSelectedShape.bind(this, newPolygon));                    
                google.maps.event.addListener(polygon.getPath(), 'set_at', this.onPolygonDrawEnd.bind(this));
                google.maps.event.addListener(polygon.getPath(), 'insert_at', this.onPolygonDrawEnd.bind(this));
            }
        }
    }

    drawPolygon(options) {
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
        this.onMapFitbounds(polygon.getPath());
        return polygon;
    }

    overlayCompleted(event) {
        var self = this;
        self.drawing_manager.setDrawingMode(null);
        var uniqueId = new Date().getTime();
        
        var newPolygon = event.overlay;
        newPolygon.type = event.type;
        newPolygon._polygonId = uniqueId;
        self.selectedPolygons[uniqueId] = newPolygon;
        
        self.setSelectedShape(newPolygon);
        self.onDrawTriggerCommit();
        google.maps.event.addListener(newPolygon, 'dblclick', this.setSelectedShape.bind(this, newPolygon));     
    }

    setSelectedShape(newPolygon) {
        this.selectedPolygon = newPolygon;
        this.selectedPolygon.setEditable(true);
    }

    clearSelectedShape(){
        if (this.selectedPolygon) {
            this.selectedPolygon.setEditable(false);
            this.selectedPolygon = null;
        }
    }

    loadSearchControls(){
        var self = this;            
        if (this.$btnSearchInput === undefined) {
            this.$btnSearchInput = $(qweb.render('GmapSearchInput', {
                widget: this
            }));
            
            const searchBox = new google.maps.places.SearchBox(this.$btnSearchInput.get(0));
            this.gmap.controls[google.maps.ControlPosition.TOP_LEFT].push(this.$btnSearchInput.get(0));
            
            this.gmap.addListener("bounds_changed", () => {
                searchBox.setBounds(this.gmap.getBounds());
            });

            searchBox.addListener("places_changed", () => {
                searchBox.set('map', null);
                
                const places = searchBox.getPlaces();
                if (places.length == 0) {
                    return;
                }
                var bounds = new google.maps.LatLngBounds();
                var i, place;
                for (i = 0; place = places[i]; i++) {
                    (function(place) {
                        var marker = new google.maps.Marker({
                            position: place.geometry.location
                        });
                        marker.bindTo('map', searchBox, 'map');
                        google.maps.event.addListener(marker, 'map_changed', function() {
                        if (!this.getMap()) {
                            this.unbindAll();
                        }
                        });
                        bounds.extend(place.geometry.location);


                    }(place));
                }
                this.gmap.fitBounds(bounds);
                searchBox.set('map', self.gmap);
                this.gmap.setZoom(Math.min(this.gmap.getZoom(),12));
            });
        }            
    }

    onPolygonDrawEnd() {
        var paths = this.selectedPolygon.getPath();
        var paths_latLng = [];
        if (paths.length > 0) {
            for (var i = 0; i < paths.getLength(); i++) {
                paths_latLng.push({
                    'lat': paths.getAt(i).lat(),
                    'lng': paths.getAt(i).lng(),
                });
            }
        }
        this.onFieldChanged({
            'type': this.selectedPolygon.type,
            'options': {paths: paths_latLng},
        });
    }

    onDrawTriggerCommit() {
        if (Object.keys(this.selectedPolygons) && Object.keys(this.selectedPolygons).length > 1) {
            this.notification.add(
                this.env._t('Only one shape is allowed for drawing!')
            );
            return;
        }
        if (this.selectedPolygon.type === 'polygon') {
            this.onPolygonDrawEnd();
        }             
    }

    onMapFitbounds(paths,bounds) {
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
    }

    deleteSelectedShape(event) {
        event.preventDefault();
        event.stopPropagation();
        if (this.selectedPolygon) {
            delete this.selectedPolygons[this.selectedPolygon._polygonId];
            this.selectedPolygon.setMap(null);
            this.onFieldChanged();
        }else{
            this.notification.add(
                this.env._t('Please select a Shape.')
            );
        }
    }

    onFieldChanged(shape_paths) {
        if (shape_paths){
            var _newValue = JSON.stringify(shape_paths);
            this.props.update(_newValue);
        }else{
            this.props.update(false);
        }
    }

}
GeofenceDrawing.template = "GeofenceDrawingView";

registry.category("fields").add("geofence_drawing", GeofenceDrawing);