from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class QuickbooksController(http.Controller):

    @http.route('/quickbook/callback', type='http', auth='public', csrf=False)
    def quickbook_callback(self, **kwargs):
        try:
            code = kwargs.get('code')
            state = kwargs.get('state')  # state = record ID
            _logger.info("QuickBooks Callback received: code=%s, state=%s", code, state)

            if code and state:
                record = request.env['oqb.instance'].sudo().browse(int(state))
                if record.exists():
                    record.sudo().write({
                        'authorize_code': code,
                    })
                    _logger.info("Authorization code saved to quickbook.auth record %s", record.id)
                    return request.redirect(f"/web#id={record.id}&model=oqb.instance&view_type=form")
                else:
                    return "Invalid state: record not found."
            return "Authorization Code Not Found"

        except Exception as e:
            _logger.exception("Error in QuickBooks callback")
            return "An error occurred during QuickBooks authorization."
