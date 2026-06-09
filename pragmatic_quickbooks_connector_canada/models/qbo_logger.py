from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class QBOLogger(models.Model):
    _name = 'qbo.logger'
    _rec_name = 'odoo_name'
    _description = 'QBO Logger'
    _order = 'created_date desc'

    odoo_name = fields.Char('Name', required=True)
    odoo_object = fields.Char('Object', required=True)
    message = fields.Char('Message', required=True)
    activity = fields.Char('Activity')
    created_date = fields.Datetime('Created Date')


    def get_today_logs(self):
        # Get the start of today (midnight in UTC)
        today_start = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, datetime.combine(datetime.today(), datetime.min.time())))

        tomorrow_start = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, datetime.combine(
            datetime.today() + timedelta(days=1), datetime.min.time())))

        # Search for logs that are older than today
        old_logs = self.search([
            '|',
            ('created_date', '<', today_start),  # Logs created before today
            ('created_date', '>=', tomorrow_start)  # Logs created tomorrow
        ])
        # Delete old logs
        old_logs.unlink()





