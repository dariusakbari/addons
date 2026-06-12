/* eslint-disable */
/*
 * Mobile shell for the EH attendance suite. Vanilla JS, no Odoo web
 * framework dependency, so the mobile clock-in works on locked-down
 * corporate browsers and basic Android / iOS WebViews.
 */
(function (global) {
    'use strict';

    var TOKEN_KEY = 'eh_mobile_device_token_v1';

    function $(sel) { return document.querySelector(sel); }
    function show(screen) {
        document.querySelectorAll('.eh-screen').forEach(function (el) { el.classList.add('eh-hidden'); });
        var el = document.querySelector('.eh-screen[data-screen="' + screen + '"]');
        if (el) el.classList.remove('eh-hidden');
    }
    function getToken() { return localStorage.getItem(TOKEN_KEY); }
    function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
    function clearToken() { localStorage.removeItem(TOKEN_KEY); }

    function authHeaders() {
        return { 'X-EH-Mobile-Token': getToken() || '' };
    }

    function postJson(url, body, extraHeaders) {
        var headers = Object.assign({ 'Content-Type': 'application/json' }, extraHeaders || {});
        return fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body || {}),
        }).then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); });
    }
    function getJson(url, extraHeaders) {
        return fetch(url, { method: 'GET', headers: extraHeaders || {} })
            .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); });
    }

    function getPosition() {
        if (!navigator.geolocation) return Promise.resolve(null);
        return new Promise(function (resolve) {
            navigator.geolocation.getCurrentPosition(
                function (p) { resolve({ lat: p.coords.latitude, lng: p.coords.longitude, accuracy: p.coords.accuracy }); },
                function () { resolve(null); },
                { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
            );
        });
    }

    function setStatus(msg) {
        var el = $('#eh-clock-status');
        if (el) el.textContent = msg || '';
    }

    function doPair() {
        var labelEl = $('#eh-pair-label');
        var pinEl = $('#eh-pair-pin');
        var errEl = $('#eh-pair-error');
        errEl.textContent = '';
        var pin = (pinEl.value || '').trim();
        if (!pin) { errEl.textContent = 'Enter the pairing PIN.'; return; }
        var label = (labelEl.value || '').trim() || 'Mobile device';
        postJson('/eh_hr/mobile/pair', { pin: pin, device_label: label }).then(function (res) {
            if (res.status !== 200) {
                errEl.textContent = (res.body && res.body.error) || ('Pairing failed (' + res.status + ').');
                return;
            }
            setToken(res.body.device_token);
            $('#eh-clock-name').textContent = 'Hi, ' + (res.body.employee_name || '');
            show('clock');
        }).catch(function (e) {
            errEl.textContent = 'Network error: ' + e.message;
        });
    }

    function doClock() {
        setStatus('Reading location...');
        getPosition().then(function (pos) {
            setStatus('Sending...');
            var body = { lat: null, lng: null };
            if (pos) { body.lat = pos.lat; body.lng = pos.lng; }
            return postJson('/eh_hr/mobile/clock', body, authHeaders());
        }).then(function (res) {
            if (res.status === 401) {
                clearToken();
                show('pair');
                return;
            }
            if (res.body && res.body.ok) {
                $('#eh-result-title').textContent = res.body.action === 'check_in' ? 'Clocked in' : 'Clocked out';
                $('#eh-result-time').textContent = new Date().toLocaleTimeString();
                $('#eh-result-detail').textContent = res.body.employee_name || '';
                show('result');
            } else {
                var reason = (res.body && res.body.reason) || 'unknown';
                var msg = {
                    'geofence_required': 'Location permission is required.',
                    'geofence_violation': 'You are not inside any of your work sites.',
                }[reason] || 'Clock failed.';
                $('#eh-result-title').textContent = 'Not allowed';
                $('#eh-result-time').textContent = '';
                $('#eh-result-detail').textContent = msg;
                show('result');
            }
        }).catch(function (err) {
            setStatus('Error: ' + err.message);
        });
    }

    function doUnpair() {
        clearToken();
        show('pair');
    }

    function init() {
        var token = getToken();
        if (!token) {
            show('pair');
            $('#eh-pair-submit').addEventListener('click', doPair);
            $('#eh-pair-pin').addEventListener('keydown', function (e) { if (e.key === 'Enter') doPair(); });
            return;
        }
        getJson('/eh_hr/mobile/whoami', authHeaders()).then(function (res) {
            if (res.status !== 200) {
                clearToken();
                show('pair');
                $('#eh-pair-submit').addEventListener('click', doPair);
                return;
            }
            $('#eh-clock-name').textContent = 'Hi, ' + (res.body.employee_name || '');
            show('clock');
            $('#eh-clock-action').addEventListener('click', doClock);
            $('#eh-clock-unpair').addEventListener('click', doUnpair);
            $('#eh-result-back') && $('#eh-result-back').addEventListener('click', function () { show('clock'); setStatus(''); });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})(typeof window !== 'undefined' ? window : this);
