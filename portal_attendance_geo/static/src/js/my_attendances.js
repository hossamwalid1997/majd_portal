odoo.define('portal_attendance_geo.my_attendances', function (require) {
    "use strict";

    var MyAttendances = require('hr_attendance.my_attendances');
    var session = require("web.session");
    var Dialog = require('web.Dialog');

    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    const { loadJS } = require('@web/core/assets');

    var MyAttendances = MyAttendances.include({
        cssLibs: [

        ],
        jsLibs: [

        ],
        events: _.extend({}, MyAttendances.prototype.events, {
            'click .gmap_kisok_toggle': '_toggle_gmap',
            'click .gip_kisok_toggle': '_toggle_gip',
            'click .glocation_kisok_toggle': '_toggle_glocation',
            'change .oe_attendance_reasons': '_on_change_reason',
        }),
        
        willStart: function () {
            var self = this;
            var superDef = this._super.apply(this, arguments);            
            var def1 = this._rpc({
                model: 'hr.attendance.reasons',
                method: 'search_read',
                args: [[], ['id','name', 'attendance_state']],
            }).then(function (reasons) {
                self.reasons = reasons;
            });     
            var def2 = this._rpc({
                route: '/portal_attendance_geo/_get_gmap_api_key',
            }).then(function (data) {                
                self._gmp_api_key_prom = JSON.parse(data).gmap_api_key || '';                                
            });
                   
            return Promise.all([superDef, def1, def2]).then(async function(){
                try {
                    if (self._gmp_api_key_prom){
                        var url = `https://maps.googleapis.com/maps/api/js?key=${self._gmp_api_key_prom}&libraries=drawing,places,geometry`;                
                        await loadJS(url);
                    }
                }
                catch (_err) {
                    console.log(_err);
                }
            });
        },
        start: function () {
            var self = this;
            this.gmap = null;
            this.ip = null;            
            return this._super.apply(this, arguments).then(function () {
                if (window.location.protocol == 'https:') {
                    self.$('.o_hr_attendance_sign_in_out_icon').css('pointer-events','none');

                    self.def_geofence = $.Deferred();
                    if (session.hr_attendance_geofence) {
                        self._initMap();
                    } else {
                        self.$('.gmap_kisok_container').css('display','none');
                        self.def_geofence.resolve();
                    }

                    self.def_ipaddress = $.Deferred();
                    if (session.hr_attendance_ip) {                    
                        self._getUserIP();
                    }else {
                        self.$('.gip_kisok_container').css('display','none');
                        self.def_ipaddress.resolve();
                    }

                    self.def_geolocation = $.Deferred();
                    if (session.hr_attendance_geolocation) {
                        self._getGeolocation();
                    }else{
                        self.$('.glocation_kisok_container').css('display','none');
                        self.def_geolocation.resolve();
                    }

                    $.when(self.def_geofence, self.def_ipaddress, self.def_geolocation).then(function(){
                        self.$('.o_hr_attendance_sign_in_out_icon').css('pointer-events','');
                    })
                }

                self.def_reason = $.Deferred();
                if (session.hr_attendance_reason) {                    
                    self._showReasons();
                }else{
                    self.$('.attendance_reason').css('display', 'none');
                    self.def_reason.resolve();
                }
            });
        },
        on_attach_callback: function () {
            this._super.apply(this, arguments);
        },
        _toggle_gmap: function () {
            var self = this;
            if (self.$(".gmap_kisok_toggle").hasClass('fa-angle-double-down')) {
                self.$('.gmap_kisok_view').toggle('show');
                self.$("i.gmap_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
                self.$(".o_hr_attendance_kiosk_backdrop")[0].setAttribute('style', 'height: calc(100vh + 197px);');
            } else {
                self.$('.gmap_kisok_view').toggle('hide');
                self.$("i.gmap_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");
                self.$(".o_hr_attendance_kiosk_backdrop")[0].setAttribute('style', 'height: calc(100vh);');
            }
        },
        _toggle_gip: function () {
            var self = this;
            if (self.$(".gip_kisok_toggle").hasClass('fa-angle-double-down')) {
                self.$('.gip_kisok_view').toggle('show');
                self.$("i.gip_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
                if (self.ip){
                    self.$('.gip_kisok_view span')[0].innerText =  "IP: " + self.ip;
                }
            } else {
                self.$('.gip_kisok_view').toggle('hide');
                self.$("i.gip_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");                
            }
        },
        _toggle_glocation: function () {
            var self = this;
            if (self.$(".glocation_kisok_toggle").hasClass('fa-angle-double-down')) {
                self.$('.glocation_kisok_view').toggle('show');
                self.$("i.glocation_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
                if (self.latitude && self.longitude){
                    self.$('.glocation_kisok_view span')[0].innerText =  "Lattitude:" + self.latitude + ", Longitude:" + self.longitude ;
                }
            } else {
                self.$('.glocation_kisok_view').toggle('hide');
                self.$("i.glocation_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");                
            }
        },
        _showReasons: function(){
            var self = this;            
            self.$('.attendance_reason').css('display', '');
            self.def_reason.resolve();
        },
        _on_change_reason: function(){
            var self = this;
            var inputReason = this.$('.oe_attendance_reasons')[0];
            if (inputReason.value !== '') {                    
                self.attendance_reason = inputReason.value;
            }
        },
        _initMap: function () {
            var self = this;
            if (window.location.protocol == 'https:') {
                var options = {
                    enableHighAccuracy: true,
                    maximumAge: 30000,
                    timeout: 27000
                };
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
                } else {
                    self.geolocation = false;
                }

                function successCallback(position) {
                    self.latitude = position.coords.latitude;
                    self.longitude = position.coords.longitude;
                    if (!self.gmap && window.google != undefined) {
                        var gmap_div = self.$('.gmap_kisok_view').get(0);
                        $(gmap_div).css({
                            width: '425px !important',
                            height: '200px !important',
                        });
                        
                        self.gmap = new google.maps.Map(gmap_div, {
                            center: { lat: self.latitude, lng: self.longitude },
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
                        self.marker = new google.maps.Marker({
                            position:  { lat: self.latitude, lng: self.longitude },
                            map: self.gmap,
                        });

                        var myPlace = new google.maps.LatLng(self.latitude, self.longitude);
                        var bounds = new google.maps.LatLngBounds();
                        bounds.extend(myPlace);
                        self.gmap.fitBounds(bounds);
                        
                        self.$('.gmap_kisok_view').toggle('slow');
                    }
                    self.$('.gmap_kisok_container').css('display', '');
                    self.def_geofence.resolve();
                }

                function errorCallback(err) {                    
                    switch (err.code) {
                        case err.PERMISSION_DENIED:
                            console.log("The request for geolocation was refused by the user.");
                            break;
                        case err.POSITION_UNAVAILABLE:
                            console.log("There is no information about the location available.");
                            break;
                        case err.TIMEOUT:
                            console.log("The request for the user's location was unsuccessful.");
                            break;
                        case err.UNKNOWN_ERROR:
                            console.log("An unidentified error has occurred.");
                            break;
                    }
                    self.def_geofence.resolve();
                }
            }
            else {
                self.$('.gmap_kisok_container').addClass('d-none');
                self.do_notify(false, _t("GEOLOCATION API MAY ONLY WORKS WITH HTTPS CONNECTIONS."));
            }
        },
        _getUserIP: function (onNewIP) {
            var self = this;

            var IP = $.get('https://www.cloudflare.com/cdn-cgi/trace',function(data) {
                data = data.trim().split('\n').reduce(function(obj, pair) {
                    pair = pair.split('=');
                    return obj[pair[0]] = pair[1], obj;
                }, {});
                if (data['ip']){
                    self.ip = data['ip'];
                    self.$('.gip_kisok_container').css('display', '');
                    self.def_ipaddress.resolve();
                }
            });

            setTimeout(function(){ 
                IP.abort(); 
                self.ip = 'Timeout error, IP not found!';
                self.$('.gip_kisok_container').css('display', '');
                self.def_ipaddress.resolve();
            }, 7000);
        },
        _getGeolocation: function () {
            var self = this;
            var options = {
                enableHighAccuracy: true,
                maximumAge: 30000,
                timeout: 27000
            };
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
            } else {
                self.geolocation = false;
                self.def_geolocation.resolve();
            }

            function successCallback(position) {
                self.latitude = position.coords.latitude;
                self.longitude = position.coords.longitude;
                self.$('.glocation_kisok_container').css('display','');
                self.def_geolocation.resolve();
            }

            function errorCallback(err) {
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        console.log("The request for geolocation was refused by the user.");
                        break;
                    case err.POSITION_UNAVAILABLE:
                        console.log("There is no information about the location available.");
                        break;
                    case err.TIMEOUT:
                        console.log("The request for the user's location was unsuccessful.");
                        break;
                    case err.UNKNOWN_ERROR:
                        console.log("An unidentified error has occurred.");
                        break;
                }
                self.def_geolocation.reject();
            }            
        },
        update_attendance: function () {
            var self = this;
            if (window.location.protocol == 'https:') {
                self._validate_attendances();
            }else {
                this._rpc({
                    model: 'hr.employee',
                    method: 'attendance_manual',
                    args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                })
                .then(function(result) {
                    if (result.action) {
                        var action = result.action;
                        self.do_action(action); 
                        var employee_id = action.attendance.employee_id[0];
                        var attendance_id = action.attendance['id'];
                        self._rpc({
                            model: 'hr.attendance',
                            method: 'update_reason',
                            args: [[attendance_id],employee_id,self.attendance_reason],
                        });
                    } else if (result.warning) {
                        self.do_warn(result.warning);
                    }
                });
            }
        },
        _validate_attendances: function(){
            var self = this;

            self.data_ip_address = null;
            self.data_latitude = null;
            self.data_longitude = null;
            self.data_is_inside = false;
            self.data_geofence_ids = null;          
            self.data_photo = false;          

            self.def_geolocation_data = new $.Deferred();
            if (session.hr_attendance_geolocation) {                
                if (window.location.protocol == 'https:') {
                self._validate_Geolocation();
            }else{
                self.def_geolocation_data.resolve();
            }
            }else{
                self.def_geolocation_data.resolve();
            }

            self.def_geofence_data = new $.Deferred();
            if (session.hr_attendance_geofence) {                
                if (window.location.protocol == 'https:') {
                self._validate_Geofence();
            }else{
                self.def_geofence_data.resolve();
            }
            }else{
                self.def_geofence_data.resolve();
            }

            self.def_ip_data = new $.Deferred();
            if (session.hr_attendance_ip) {                    
                if (window.location.protocol == 'https:') {                   
                self._validate_IP();
            }else{
                self.def_ip_data.resolve();
            }
            }else{
                self.def_ip_data.resolve();
            }
            
            self.def_photo_data = new $.Deferred();
            if (session.hr_attendance_photo) {                
                if (window.location.protocol == 'https:') {
                self._validate_Photo();
            }else{
                self.def_photo_data.resolve();
            }
            }else{
                self.def_photo_data.resolve();
            }

            $.when(self.def_geolocation_data, self.def_geofence_data, self.def_ip_data,self.def_photo_data).then(function(){
                self._manual_attendance(self.data_ip_address, self.data_latitude, self.data_longitude, self.data_is_inside, self.data_geofence_ids, self.data_photo);
            })
        },
        _validate_Photo: function () {
            var self = this;
            this.dialogPhoto = new Dialog(this, {
                size: 'medium',
                title: _t("Capture Snapshot"),
                $content: `
                <div class="container-fluid">
                    <div class="col-12 controls">
                        <fieldset class="reader-config-group">
                            <div class="row mb8">
                                <div class="col-3">
                                    <label>
                                        <span>Select Camera</span>
                                    </label>
                                </div>
                                <div class="col-6">
                                    <select name="video_source" class="videoSource" id="videoSource">                                       
                                    </select>
                                </div>
                                <div class="col-3">
                                </div>
                            </div>
                        </fieldset>
                    </div>
                    <div class="row">                                
                        <div class="col-12" id="videoContainer">
                            <video autoplay muted playsinline id="video" style="width: 100%; max-height: 100%; box-sizing: border-box;" autoplay="1"/>
                            <canvas id="image" style="display: none;"/>
                        </div>
                    </div>
                </div>`,
                buttons: [
                    {
                        text: _t("Capture Snapshot"), classes: 'btn-primary captureSnapshot',
                    },
                    {
                        text: _t("Close"), classes: 'btn-secondary captureClose', close: true,
                    }
                ]
            }).open();

            this.dialogPhoto.opened().then(async function () {
                var videoElement = self.dialogPhoto.$('#video').get(0);
                var videoSelect = self.dialogPhoto.$('select#videoSource').get(0);
                videoSelect.onchange = getStream;

                getStream().then(getDevices).then(gotDevices);

                function getStream() {
                    if (window.stream) {
                        window.stream.getTracks().forEach(track => {
                            track.stop();
                        });
                    }
                    const videoSource = videoSelect.value;
                    const constraints = {
                        video: { deviceId: videoSource ? { exact: videoSource } : undefined }
                    };
                    return navigator.mediaDevices.getUserMedia(constraints).then(gotStream).catch(handleError);
                }

                function getDevices() {
                    return navigator.mediaDevices.enumerateDevices();
                }

                function gotDevices(deviceInfos) {
                    window.deviceInfos = deviceInfos;
                    for (const deviceInfo of deviceInfos) {
                        const option = document.createElement('option');
                        option.value = deviceInfo.deviceId;
                        if (deviceInfo.kind === 'videoinput') {
                            option.text = deviceInfo.label || "Camera" + (videoSelect.length + 1) + "";
                            videoSelect.appendChild(option);
                        }
                    }
                }

                function gotStream(stream) {
                    window.stream = stream;
                    videoSelect.selectedIndex = [...videoSelect.options].
                        findIndex(option => option.text === stream.getVideoTracks()[0].label);
                    videoElement.srcObject = stream;
                }

                function handleError(error) {
                    console.error('Error: ', error);
                }

                var $captureSnapshot = self.dialogPhoto.$footer.find('.captureSnapshot');
                var $closeBtn = self.dialogPhoto.$footer.find('.captureClose');

                $captureSnapshot.on('click', function (event) {
                    var img64 = "";
                    var image = self.dialogPhoto.$('#image').get(0);
                    image.width = $(video).width();
                    image.height = $(video).height();
                    image.getContext('2d').drawImage(video, 0, 0, image.width, image.height);
                    var img64 = image.toDataURL("image/jpeg");
                    img64 = img64.replace(/^data:image\/(png|jpg|jpeg|webp);base64,/, "");
                    if (img64) {
                        self.data_photo = img64;
                        self.def_photo_data.resolve();
                        if (window.stream) {
                            window.stream.getTracks().forEach(track => {
                                track.stop();
                            });
                        }
                        $closeBtn.click();
                    }else{
                        self.def_photo_data.reject();
                    }
                    $captureSnapshot.text("uploading....").addClass('disabled');
                });

            });
        },
        _validate_Geolocation: function(){
            var self = this;
            if (self.latitude && self.longitude){
                self.data_latitude = self.latitude || null;
                self.data_longitude = self.longitude || null;
                self.def_geolocation_data.resolve();
            }else{
                self.def_geolocation_data.reject();
            }     
        },
        _validate_IP: function(){
            var self = this;
            if (self.ip ){
                self.data_ip_address = self.ip || null;
                self.def_ip_data.resolve();
            }else{
                self.def_ip_data.reject();
            }     
        },
        _validate_Geofence: async function(){
            var self = this;
            var insidePolygon = false;
            var insideGeofences = []              
            
            await self._rpc({
                model: 'hr.attendance.geofence',
                method: 'search_read',
                args: [[['company_id', '=', self.getSession().company_id], ['employee_ids', 'in', self.employee.id]], ['id', 'name', 'shape_paths']],
            }).then(function (res) {                    
                self.geofence_data = res.length && res;                
                if (!res.length) {
                    self.def_geofence_data.reject();
                }
                
                var options = {
                    enableHighAccuracy: true,
                    maximumAge: 30000,
                    timeout: 27000
                };
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
                }
                    
                function successCallback(position) {
                    self.latitude = position.coords.latitude;
                    self.longitude = position.coords.longitude;
                    if (self.gmap) {
                        for (let i = 0; i < self.geofence_data.length; i++) {
                            var path = self.geofence_data[i].shape_paths;                            
                            var value = JSON.parse(path);                                
                            if (Object.keys(value).length > 0) {
                                
                                var polygonOptions = {
                                    editable: false,
                                    map: self.gmap,
                                    strokeColor: '#FF0000',
                                    strokeOpacity: 0.86,
                                    strokeWeight: 1.1,
                                    fillColor: '#FF9999',
                                    fillOpacity: 0.34,
                                }
                                const polygon = new google.maps.Polygon(polygonOptions);
                                polygon.setOptions(value.options);

                                const insidePolygon = google.maps.geometry.poly.containsLocation(
                                    { lat: self.latitude, lng: self.longitude },
                                    polygon
                                )
                                if (insidePolygon === true) {
                                    insideGeofences.push(self.geofence_data[i].id);
                                }
                            }
                        }
                        
                        if (insideGeofences.length > 0) {
                            self.data_is_inside = true;
                            self.data_geofence_ids = insideGeofences;
                            self.def_geofence_data.resolve();
                        } else {
                            Swal.fire({
                                title: 'Access Denied',
                                text: "You haven't entered any of the geofence zones.",
                                icon: 'error',
                                confirmButtonColor: '#3085d6',
                                confirmButtonText: 'Ok'
                            }).then(function(){
                                if(self.dialogPhoto && self.dialogPhoto != undefined){
                                    var $closeBtn = self.dialogPhoto.$footer.find('.captureClose');
                                    if (window.stream) {
                                        window.stream.getTracks().forEach(track => {
                                            track.stop();
                                        });
                                    }
                                    $closeBtn.click()
                                }
                            });
                            self.def_geofence_data.reject();
                        }
                    }
                }
                function errorCallback(err) {
                    console.log(err);
                }
            })
        },
        
        _manual_attendance: function (data_ip_address, data_latitude, data_longitude, data_geofence_ids, data_photo) {
            var self = this;
            var data_ip_address = self.data_ip_address || null;
            var data_latitude = self.data_latitude || null;
            var data_longitude = self.data_longitude || null;
            var data_geofence_ids = self.data_geofence_ids || null;
            var data_photo = self.data_photo || null;

            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', null, [data_latitude, data_longitude], data_ip_address, data_geofence_ids, [data_photo]],
            }).then(function (result) {
                if (result.action) {
                    var action = result.action;
                    self.do_action(action); 
                    var employee_id = action.attendance.employee_id[0];
                    var attendance_id = action.attendance['id'];
                    self._rpc({
                        model: 'hr.attendance',
                        method: 'update_reason',
                        args: [[attendance_id],employee_id,self.attendance_reason],
                    });
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
        },
    });
});
