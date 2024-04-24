odoo.define('sb_geo_attendance_portal.sb_geo_attendance_portal', function (require) {
    "use strict";

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var session = require("web.session");
    var _t = core._t;

    const { loadJS } = require('@web/core/assets');

    publicWidget.registry.PortalAttendanceHome = publicWidget.Widget.extend({
        selector: '.o_portal_my_home',
        events: {
            "click .o_hr_attendance_sign_in_out_icon": "_onClickInOut",
        },

        // Was added In Odoo 16
        // start: function () {
        //     var def = this._super.apply(this, arguments);
        //     this.el.querySelector('.o_portal_no_doc_message').classList.add('d-none');
        //     return def;
        // },

        _onClickInOut: function (ev) {
            ev.preventDefault();
            window.location.href = '/my/hr_attendances/create_new';
        },

    });

    publicWidget.registry.PortalAttendanceHomeControllers = publicWidget.Widget.extend({
        selector: '#wrapwrap:has(.p_o_hr_attendance_kiosk_mode_container)',
        cssLibs: [

        ],
        jsLibs: [

        ],
        events: {
            "click .p_o_hr_attendance_sign_in_out_icon": _.debounce(function () {
                this.update_attendance();
            }, 200, true),
            // 'click .p_o_gmap_kisok_toggle': '_toggle_gmap',
            // 'click .p_o_gip_kisok_toggle': '_toggle_gip',
            // 'click .p_o_glocation_kisok_toggle': '_toggle_glocation',
            // 'change .p_o_attendance_reasons': '_on_change_reason',
        },
        custom_events: {
        },
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.employee_id = $('input#employee_input').data('employee_id') || false;
            this.company_id = $('input#employee_input').data('company_id') || false;
            this.user_id = $('input#employee_input').data('user_id') || false;
            // this.hr_attendance_geolocation = $('input#employee_input').data('hr_attendance_geolocation') ? true : false;
            // this.hr_attendance_geofence = $('input#employee_input').data('hr_attendance_geofence') ? true : false;
            // this.hr_attendance_photo = $('input#employee_input').data('hr_attendance_photo') ? true : false;
            // this.hr_attendance_ip = $('input#employee_input').data('hr_attendance_ip') ? true : false;
            // this.hr_attendance_reason = $('input#employee_input').data('hr_attendance_reason') ? true : false;
            // this.isInside = false;
            // this.insideGeofences = false;
            // this.gmap = null;
        },
        willStart: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            var def1 = this._rpc({
                route: '/sb_geo_attendance_portal/search_read/get_employee_data',
                params: {
                    'employee_id': parseInt(this.employee_id),
                },
            }).then(function (res) {
                self.employee = res.length && res[0];
            })
            // return Promise.all([def, def1])
            // var def2 = this._rpc({
            //     route: '/portal_attendance_geo/_get_gmap_api_key',
            // }).then(function (data) {
            //     self._gmp_api_key_prom = JSON.parse(data).gmap_api_key || '';
            // });
            // return Promise.all([def, def1, def2]).then(async function(){
            //     var url = `https://maps.googleapis.com/maps/api/js?key=${self._gmp_api_key_prom}&libraries=drawing,places,geometry`;
            //     await loadJS(url);
            // });
            return Promise.all([
                def, def1
            ]);

        },
        start: function () {
            var self = this;

            return this._super.apply(this, arguments).then(function () {
                // if (window.location.protocol == 'https:') {
                //
                //     $("a.hr_attendance_sign_out_icon").css('pointer-events','none');
                //     $("a.hr_attendance_sign_in_icon").css('pointer-events','none');
                //
                //     self.def_geofence = $.Deferred();
                //     if (self.hr_attendance_geofence) {
                //         self._initMap();
                //     } else {
                //         self.$('.p_o_gmap_kisok_container').css('display','none');
                //         self.def_geofence.resolve();
                //     }
                //
                //     self.def_ipaddress = $.Deferred();
                //     if (self.hr_attendance_ip) {
                //         self._getUserIP();
                //     }else {
                //         self.$('.p_o_gip_kisok_container').css('display','none');
                //         self.def_ipaddress.resolve();
                //     }
                //
                //     self.def_geolocation = $.Deferred();
                //     if (self.hr_attendance_geolocation) {
                //         self._getGeolocation();
                //     }else{
                //         self.$('.p_o_glocation_kisok_container').css('display','none');
                //         self.def_geolocation.resolve();
                //     }
                //
                //     $.when(self.def_geofence, self.def_ipaddress, self.def_geolocation).then(function(){
                //         $("a.hr_attendance_sign_out_icon").css('pointer-events','');
                //         $("a.hr_attendance_sign_in_icon").css('pointer-events','');
                //     })
                // }

                // self.def_reason = $.Deferred();
                // if (self.hr_attendance_reason) {
                //     self._showReasons();
                // }else{
                //     self.$('.attendance_reason').css('display', 'none');
                //     self.def_reason.resolve();
                // }

                var hrs_today =  0.00;
                if (self.employee && self.employee.hours_today != undefined){
                    self.convertNumToTime(self.employee.hours_today);
                }


                if (self.employee && self.employee.attendance_state == 'checked_in') {
                    $("a.hr_attendance_sign_out_icon").hide();
                    $("a.hr_attendance_sign_in_icon").show();

                    $(".hr_attendance_sign_out_text").show();
                    $(".hr_attendance_sign_in_text").hide();

                    $("h4.hours_today").removeClass('d-none').find('span')[0].innerText = hrs_today;
                }else if (self.employee && self.employee.attendance_state == 'checked_out') {
                    $("a.hr_attendance_sign_out_icon").show();
                    $("a.hr_attendance_sign_in_icon").hide();

                    $(".hr_attendance_sign_out_text").hide();
                    $(".hr_attendance_sign_in_text").show();
                    $("h4.hours_today").removeClass('d-none').find('span')[0].innerText = hrs_today;
                }
            })
        },
        // _showReasons: function(){
        //     var self = this;
        //     self.$('.p_o_attendance_reason').css('display', '');
        //     self.def_reason.resolve();
        // },
        // _initMap: function () {
        //     var self = this;
        //     if (window.location.protocol == 'https:') {
        //         var options = {
        //             enableHighAccuracy: true,
        //             maximumAge: 30000,
        //             timeout: 27000
        //         };
        //         if (navigator.geolocation) {
        //             navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
        //         } else {
        //             self.geolocation = false;
        //         }
        //
        //         function successCallback(position) {
        //             self.latitude = position.coords.latitude;
        //             self.longitude = position.coords.longitude;
        //             if (!self.gmap) {
        //                 var gmap_div = self.$('.p_o_gmap_kisok_view').get(0);
        //                 $(gmap_div).css({
        //                     width: '425px !important',
        //                     height: '200px !important',
        //                 });
        //
        //                 self.gmap = new google.maps.Map(gmap_div, {
        //                     center: { lat: self.latitude, lng: self.longitude },
        //                     mapTypeId: google.maps.MapTypeId.ROADMAP,
        //                     fullscreenControl: true,
        //                     mapTypeControl: true,
        //                     gestureHandling: 'cooperative',
        //                     mapTypeControlOptions: {
        //                         mapTypeIds: ['satellite', 'hybrid', 'terrain'],
        //                         style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
        //                     },
        //                     zoom: 3,
        //                     minZoom: 3,
        //                     maxZoom: 20,
        //                 });
        //                 self.marker = new google.maps.Marker({
        //                     position:  { lat: self.latitude, lng: self.longitude },
        //                     map: self.gmap,
        //                 });
        //
        //                 var myPlace = new google.maps.LatLng(self.latitude, self.longitude);
        //                 var bounds = new google.maps.LatLngBounds();
        //                 bounds.extend(myPlace);
        //                 self.gmap.fitBounds(bounds);
        //             }
        //             self.$('.p_o_gmap_kisok_container').css('display', '');
        //             self.def_geofence.resolve();
        //         }
        //
        //         function errorCallback(err) {
        //             switch (err.code) {
        //                 case err.PERMISSION_DENIED:
        //                     console.log("The request for geolocation was refused by the user.");
        //                     break;
        //                 case err.POSITION_UNAVAILABLE:
        //                     console.log("There is no information about the location available.");
        //                     break;
        //                 case err.TIMEOUT:
        //                     console.log("The request for the user's location was unsuccessful.");
        //                     break;
        //                 case err.UNKNOWN_ERROR:
        //                     console.log("An unidentified error has occurred.");
        //                     break;
        //             }
        //         }
        //     }
        //     else {
        //         self.$('.p_o_gmap_kisok_container').addClass('d-none');
        //     }
        //     return true;
        // },
        // _on_change_reason: function(){
        //     var self = this;
        //     var inputReason = this.$('.p_o_attendance_reasons')[0];
        //     if (inputReason.value !== '') {
        //         self.attendance_reason = inputReason.value;
        //     }
        // },
        // _getUserIP: function (onNewIP) {
        //     var self = this;
        //     var IP = $.get('https://www.cloudflare.com/cdn-cgi/trace',function(data) {
        //         data = data.trim().split('\n').reduce(function(obj, pair) {
        //             pair = pair.split('=');
        //             return obj[pair[0]] = pair[1], obj;
        //         }, {});
        //         if (data['ip']){
        //             self.ip = data['ip'];
        //             self.$('.p_o_gip_kisok_container').css('display', '');
        //             self.def_ipaddress.resolve();
        //         }
        //     });
        //
        //     setTimeout(function(){
        //         IP.abort();
        //         self.ip = 'Timeout error, IP not found!';
        //         self.$('.p_o_gip_kisok_container').css('display', '');
        //         self.def_ipaddress.resolve();
        //     }, 7000);
        // },
        // _getGeolocation: function () {
        //     var self = this;
        //     var options = {
        //         enableHighAccuracy: true,
        //         maximumAge: 30000,
        //         timeout: 27000
        //     };
        //     if (navigator.geolocation) {
        //         navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
        //     } else {
        //         self.geolocation = false;
        //         self.def_geolocation.reject();
        //     }
        //
        //     function successCallback(position) {
        //         self.latitude = position.coords.latitude;
        //         self.longitude = position.coords.longitude;
        //         self.$('.p_o_glocation_kisok_container').css('display','');
        //         self.def_geolocation.resolve();
        //     }
        //
        //     function errorCallback(err) {
        //         switch (err.code) {
        //             case err.PERMISSION_DENIED:
        //                 console.log("The request for geolocation was refused by the user.");
        //                 break;
        //             case err.POSITION_UNAVAILABLE:
        //                 console.log("There is no information about the location available.");
        //                 break;
        //             case err.TIMEOUT:
        //                 console.log("The request for the user's location was unsuccessful.");
        //                 break;
        //             case err.UNKNOWN_ERROR:
        //                 console.log("An unidentified error has occurred.");
        //                 break;
        //         }
        //         self.def_geolocation.reject();
        //     }
        // },
        update_attendance: function () {
            var self = this;

            console.log('It\'s Working Yaaay!!')
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                context: session.user_context,
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                    self.update_attendance_kiosk_gui()
                } else if (result.warning) {
                    self.displayNotification({ title: result.warning, type: 'danger' });
                }
            });
            // self.data_latitude = null;
            // self.data_longitude = null;
            // self.data_is_inside = false;
            // self.data_geofence_ids = null;
            // self.data_photo = false;

            // self.def_geofence_data = new $.Deferred();
            // if (self.hr_attendance_geofence) {
            //     if (window.location.protocol == 'https:') {
            //         self._validate_Geofence();
            //     }else{
            //         self.def_geofence_data.resolve();
            //     }
            // }else{
            //     self.def_geofence_data.resolve();
            // }

            // self.def_geolocation_data = new $.Deferred();
            // if (self.hr_attendance_geolocation) {
            //     if (window.location.protocol == 'https:') {
            //         self._validate_Geolocation();
            //     }else{
            //         self.def_geolocation_data.resolve();
            //     }
            // }else{
            //     self.def_geolocation_data.resolve();
            // }

            // self.def_photo_data = new $.Deferred();
            // if (self.hr_attendance_photo) {
            //     if (window.location.protocol == 'https:') {
            //         self._validate_Photo();
            //     }else{
            //         self.def_photo_data.resolve();
            //     }
            // }else{
            //     self.def_photo_data.resolve();
            // }

            // $.when(self.def_geolocation_data, self.def_geofence_data, self.def_photo_data).then(function(){
            //     self._manual_attendance(self.data_latitude, self.data_longitude, self.data_geofence_ids, self.data_ip_address , self.data_photo);
            // })
        },
        // _validate_Geolocation: function(){
        //     var self = this;
        //     if (self.latitude && self.longitude){
        //         self.data_latitude = self.latitude || null;
        //         self.data_longitude = self.longitude || null;
        //         self.def_geolocation_data.resolve();
        //     }else{
        //         self.def_geolocation_data.reject();
        //     }
        // },
        // _validate_Geofence: async function(){
        //     var self = this;
        //     var insidePolygon = false;
        //     var insideGeofences = []
        //
        //     await self._rpc({
        //         model: 'hr.attendance.geofence',
        //         method: 'search_read',
        //         args: [[['company_id', '=', self.employee.company_id[0]], ['employee_ids', 'in', self.employee.id]], ['id', 'name', 'shape_paths']],
        //     }).then(function (res) {
        //         self.geofence_data = res.length && res;
        //         if (!res.length) {
        //             self.def_geofence_data.reject();
        //         }
        //
        //         var options = {
        //             enableHighAccuracy: true,
        //             maximumAge: 30000,
        //             timeout: 27000
        //         };
        //         if (navigator.geolocation) {
        //             navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
        //         }
        //
        //         function successCallback(position) {
        //             self.latitude = position.coords.latitude;
        //             self.longitude = position.coords.longitude;
        //             if (self.gmap) {
        //                 for (let i = 0; i < self.geofence_data.length; i++) {
        //                     var path = self.geofence_data[i].shape_paths;
        //                     var value = JSON.parse(path);
        //                     if (Object.keys(value).length > 0) {
        //
        //                         var polygonOptions = {
        //                             editable: false,
        //                             map: self.gmap,
        //                             strokeColor: '#FF0000',
        //                             strokeOpacity: 0.86,
        //                             strokeWeight: 1.1,
        //                             fillColor: '#FF9999',
        //                             fillOpacity: 0.34,
        //                         }
        //                         const polygon = new google.maps.Polygon(polygonOptions);
        //                         polygon.setOptions(value.options);
        //
        //                         const insidePolygon = google.maps.geometry.poly.containsLocation(
        //                             { lat: self.latitude, lng: self.longitude },
        //                             polygon
        //                         )
        //                         if (insidePolygon === true) {
        //                             insideGeofences.push(self.geofence_data[i].id);
        //                         }
        //                     }
        //                 }
        //
        //                 if (insideGeofences.length > 0) {
        //                     self.data_is_inside = true;
        //                     self.data_geofence_ids = insideGeofences;
        //                     self.def_geofence_data.resolve();
        //                 } else {
        //                     Swal.fire({
        //                         title: 'Access Denied',
        //                         text: "You haven't entered any of the geofence zones.",
        //                         icon: 'error',
        //                         confirmButtonColor: '#3085d6',
        //                         confirmButtonText: 'Ok'
        //                     }).then(function(){
        //                         if(self.dialogPhoto && self.dialogPhoto != undefined){
        //                             var $closeBtn = self.dialogPhoto.$footer.find('.captureClose');
        //                             if (window.stream) {
        //                                 window.stream.getTracks().forEach(track => {
        //                                     track.stop();
        //                                 });
        //                             }
        //                             $closeBtn.click()
        //                         }
        //                     });
        //                     self.def_geofence_data.reject();
        //                 }
        //             }
        //         }
        //         function errorCallback(err) {
        //             switch (err.code) {
        //                 case err.PERMISSION_DENIED:
        //                     console.log("The request for geolocation was refused by the user.");
        //                     break;
        //                 case err.POSITION_UNAVAILABLE:
        //                     console.log("There is no information about the location available.");
        //                     break;
        //                 case err.TIMEOUT:
        //                     console.log("The request for the user's location was unsuccessful.");
        //                     break;
        //                 case err.UNKNOWN_ERROR:
        //                     console.log("An unidentified error has occurred.");
        //                     break;
        //             }
        //             self.def_geofence_data.reject();
        //         }
        //     })
        // },
        //
        // _manual_attendance: function (latitude, longitude, insideGeofences, ipaddress, img64) {
        //     var self = this;
        //
        //     var data_latitude = latitude || null;
        //     var data_longitude = longitude || null;
        //     var data_geofence_ids = insideGeofences || null;
        //     var data_ip_address = ipaddress || null;
        //     var data_photo = img64|| null;
        //
        //     this._rpc({
        //         model: 'hr.employee',
        //         method: 'attendance_manual',
        //         args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', null, [data_latitude, data_longitude], data_ip_address, data_geofence_ids, [data_photo]],
        //     }).then(async function (result) {
        //         if (result.action) {
        //             var action = result.action;
        //             var employee_id = action.attendance.employee_id[0];
        //             var attendance_id = action.attendance['id'];
        //             await self._rpc({
        //                 model: 'hr.attendance',
        //                 method: 'update_reason',
        //                 args: [[attendance_id],employee_id,self.attendance_reason],
        //             }).then(function(){
        //                 self.update_attendance_kiosk_gui();
        //                 if (window.stream) {
        //                     window.stream.getTracks().forEach(track => {
        //                         track.stop();
        //                     });
        //                 }
        //             });
        //         } else if (result.warning) {
        //             this.do_notify(false, result.warning);
        //             if (window.stream) {
        //                 window.stream.getTracks().forEach(track => {
        //                     track.stop();
        //                 });
        //             }
        //         }
        //     });
        // },
        // _validate_Photo: function () {
        //     var self = this;
        //     this.dialogPhoto = new Dialog(this, {
        //         size: 'medium',
        //         title: _t("Capture Snapshot"),
        //         $content: `
        //         <div class="container-fluid">
        //             <div class="col-12 controls">
        //                 <fieldset class="reader-config-group">
        //                     <div class="row mb8">
        //                         <div class="col-3">
        //                             <label>
        //                                 <span>Select Camera</span>
        //                             </label>
        //                         </div>
        //                         <div class="col-6">
        //                             <select name="video_source" class="videoSource" id="videoSource">
        //                             </select>
        //                         </div>
        //                         <div class="col-3">
        //                         </div>
        //                     </div>
        //                 </fieldset>
        //             </div>
        //             <div class="row">
        //                 <div class="col-12" id="videoContainer">
        //                     <video autoplay muted playsinline id="video" style="width: 100%; max-height: 100%; box-sizing: border-box;" autoplay="1"/>
        //                     <canvas id="image" style="display: none;"/>
        //                 </div>
        //             </div>
        //         </div>`,
        //         buttons: [
        //             {
        //                 text: _t("Capture Snapshot"), classes: 'btn-primary captureSnapshot',
        //             },
        //             {
        //                 text: _t("Close"), classes: 'btn-secondary captureClose', close: true,
        //             }
        //         ]
        //     }).open();
        //
        //     this.dialogPhoto.opened().then(async function () {
        //         var videoElement = self.dialogPhoto.$('#video').get(0);
        //         var videoSelect = self.dialogPhoto.$('select#videoSource').get(0);
        //         videoSelect.onchange = getStream;
        //
        //         getStream().then(getDevices).then(gotDevices);
        //
        //         function getStream() {
        //             if (window.stream) {
        //                 window.stream.getTracks().forEach(track => {
        //                     track.stop();
        //                 });
        //             }
        //             const videoSource = videoSelect.value;
        //             const constraints = {
        //                 video: { deviceId: videoSource ? { exact: videoSource } : undefined }
        //             };
        //             return navigator.mediaDevices.getUserMedia(constraints).then(gotStream).catch(handleError);
        //         }
        //
        //         function getDevices() {
        //             return navigator.mediaDevices.enumerateDevices();
        //         }
        //
        //         function gotDevices(deviceInfos) {
        //             window.deviceInfos = deviceInfos;
        //             for (const deviceInfo of deviceInfos) {
        //                 const option = document.createElement('option');
        //                 option.value = deviceInfo.deviceId;
        //                 if (deviceInfo.kind === 'videoinput') {
        //                     option.text = deviceInfo.label || "Camera" + (videoSelect.length + 1) + "";
        //                     videoSelect.appendChild(option);
        //                 }
        //             }
        //         }
        //
        //         function gotStream(stream) {
        //             window.stream = stream;
        //             videoSelect.selectedIndex = [...videoSelect.options].
        //                 findIndex(option => option.text === stream.getVideoTracks()[0].label);
        //             videoElement.srcObject = stream;
        //         }
        //
        //         function handleError(error) {
        //             console.error('Error: ', error);
        //         }
        //
        //         var $captureSnapshot = self.dialogPhoto.$footer.find('.captureSnapshot');
        //         var $closeBtn = self.dialogPhoto.$footer.find('.captureClose');
        //
        //         $captureSnapshot.on('click', function (event) {
        //             var img64 = "";
        //             var image = self.dialogPhoto.$('#image').get(0);
        //             image.width = $(video).width();
        //             image.height = $(video).height();
        //             image.getContext('2d').drawImage(video, 0, 0, image.width, image.height);
        //             var img64 = image.toDataURL("image/jpeg");
        //             img64 = img64.replace(/^data:image\/(png|jpg|jpeg|webp);base64,/, "");
        //             if (img64) {
        //                 self.data_photo = img64;
        //                 self.def_photo_data.resolve();
        //                 $closeBtn.click();
        //             }else{
        //                 self.def_photo_data.reject();
        //             }
        //             $captureSnapshot.text("uploading....").addClass('disabled');
        //         });
        //
        //     });
        // },
        update_attendance_kiosk_gui: function () {
            var self = this;
            this._rpc({
                route: '/sb_geo_attendance_portal/search_read/get_employee_data',
                params: {
                    'employee_id': parseInt(this.employee_id),
                },
            }).then(function (res) {
                self.employee = res.length && res[0];
                if (res.length) {
                    var hrs_today =  0.00;
                    if (self.employee && self.employee.hours_today != undefined){
                        self.convertNumToTime(self.employee.hours_today);
                    }

                    if (self.employee && self.employee.attendance_state == 'checked_in') {
                        $("a.hr_attendance_sign_out_icon").hide();
                        $("a.hr_attendance_sign_in_icon").show();

                        $(".hr_attendance_sign_out_text").show();
                        $(".hr_attendance_sign_in_text").hide();

                        $("h4.hours_today").removeClass('d-none').find('span')[0].innerText = hrs_today;
                    }else if (self.employee && self.employee.attendance_state == 'checked_out') {
                        $("a.hr_attendance_sign_out_icon").show();
                        $("a.hr_attendance_sign_in_icon").hide();

                        $(".hr_attendance_sign_out_text").hide();
                        $(".hr_attendance_sign_in_text").show();
                        $("h4.hours_today").removeClass('d-none').find('span')[0].innerText = hrs_today;
                    }

                    self.$('.p_o_attendance_reason').css('display', 'none');

                    window.setTimeout(function(){
                        window.location = '/my/hr_attendances';
                    }, 500);
                }
            });
        },
        convertNumToTime: function (number) {
            var self = this;
            var sign = (number >= 0) ? 1 : -1;
            number = number * sign;
            var hour = Math.floor(number);
            var decpart = number - hour;

            var min = 1 / 60;
            decpart = min * Math.round(decpart / min);

            var minute = Math.floor(decpart * 60) + '';
            if (minute.length < 2) {
                minute = '0' + minute;
            }

            sign = sign == 1 ? '' : '-';
            var time = sign + hour + ':' + minute;
            return time;
        },
        // _toggle_gmap: function () {
        //     var self = this;
        //     var self = this;
        //     if (self.$(".p_o_gmap_kisok_toggle").hasClass('fa-angle-double-down')) {
        //         self.$('.p_o_gmap_kisok_view').toggle('show');
        //         self.$("i.p_o_gmap_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
        //     } else {
        //         self.$('.p_o_gmap_kisok_view').toggle('hide');
        //         self.$("i.p_o_gmap_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");
        //     }
        // },
        // _toggle_gip: function () {
        //     var self = this;
        //     if (self.$(".p_o_gip_kisok_toggle").hasClass('fa-angle-double-down')) {
        //         self.$('.p_o_gip_kisok_view').toggle('show');
        //         self.$("i.p_o_gip_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
        //         if (self.ip){
        //             self.$('.p_o_gip_kisok_view span')[0].innerText =  "IP: " + self.ip;
        //         }
        //     } else {
        //         self.$('.p_o_gip_kisok_view').toggle('hide');
        //         self.$("i.p_o_gip_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");
        //     }
        // },
        // _toggle_glocation: function () {
        //     var self = this;
        //     if (self.$(".p_o_glocation_kisok_toggle").hasClass('fa-angle-double-down')) {
        //         self.$('.p_o_glocation_kisok_view').toggle('show');
        //         self.$("i.p_o_glocation_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
        //         if (self.latitude && self.longitude){
        //             self.$('.p_o_glocation_kisok_view span')[0].innerText =  "Lattitude:" + self.latitude + ", Longitude:" + self.longitude ;
        //         }
        //     } else {
        //         self.$('.p_o_glocation_kisok_view').toggle('hide');
        //         self.$("i.p_o_glocation_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");
        //     }
        // },
    });
});
