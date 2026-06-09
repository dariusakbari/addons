from odoo import http, _
from odoo.http import request
import requests
import base64
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class Custom_Quickbook_controller(http.Controller):

    @http.route('/get_auth_code', type="http", auth="public", website=True)
    def get_auth_code(self, **kwarg):
        '''Get access Token and store in object'''
        _logger.info('POST : {} {} {}'.format(http.request.uid, request.session, kwarg))
        flag = False
        if kwarg.get('code'):
            company_id = http.request.env['res.users'].sudo().search([('id', '=', int(http.request.uid))],
                                                                       limit=1).company_id
            try:
                if company_id:
                    company_id.write({
                        'auth_code': kwarg.get('code'),
                        'realm_id': kwarg.get('realmId')
                    })
                    client_id = company_id.client_id
                    client_secret = company_id.client_secret
                    redirect_uri = company_id.request_token_url

                    raw_b64 = str(client_id) + ":" + str(client_secret)
                    raw_b64 = raw_b64.encode('utf-8')
                    converted_b64 = base64.b64encode(raw_b64).decode('utf-8')
                    auth_header = 'Basic ' + converted_b64
                    headers = {}
                    headers['Authorization'] = str(auth_header)
                    headers['accept'] = 'application/json'
                    payload = {
                        'code': str(kwarg.get('code')),
                        'redirect_uri': redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                    access_token = requests.post(company_id.access_token_url, data=payload, headers=headers)
                    _logger.info('Authentications : {}->Response Text : {} '.format(access_token,  json.loads(access_token.text)))
                    if access_token.status_code == 200:
                        parsed_token_response = json.loads(access_token.text)
                        if parsed_token_response:
                            company_id.write({
                                'access_token': parsed_token_response.get('access_token'),
                                'qbo_refresh_token': parsed_token_response.get('refresh_token'),
                                'access_token_expire_in': datetime.now() + timedelta(
                                    seconds=parsed_token_response.get('expires_in')),
                                'refresh_token_expire_in': datetime.now() + timedelta(
                                    seconds=parsed_token_response.get('x_refresh_token_expires_in'))
                            })
                            # company_id._cr.commit()
                            headers = {}
                            headers['Authorization'] = 'Bearer ' + str(company_id.access_token)
                            headers['Accept'] = 'application/json'
                            _logger.info(_("Authorized successfully...!!"))
                            flag = True
                            url = f'{company_id.url}{company_id.realm_id}/companyinfo/{company_id.realm_id}?minorversion=75'
                            company_info_response = requests.request('GET', url, headers=headers)
                            if company_info_response.status_code == 200:
                                company_data = company_info_response.json().get('CompanyInfo', {})
                                company_name = company_data.get('CompanyName')
                                _logger.info("Connected to QuickBooks Company: %s", company_name)

                                # Optionally, save company name in Odoo model
                                company_id.write({
                                    'quickbooks_company_name': company_name
                                })
                            else:
                                _logger.warning("Failed to fetch company info: %s", company_info_response.text)



                    else:
                        _logger.error("{} -> {}".format(access_token.status_code, access_token.text))
            except Exception as e:
                _logger.error("Exception : {}".format(e))
        if flag:
            return "Authenticated Successfully..!! \n You can close this window now"
        else:
            return "Something went wrong, Authentication was not completed Successfully..!!"

