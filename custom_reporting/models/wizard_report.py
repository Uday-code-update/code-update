from odoo import models, fields, api

class CommitMentOrderReport(models.TransientModel):
    _name = "commit.report.wizard"

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    st_type = fields.Selection([('category', 'Category'),
                                ('commit_order', 'Commitment Order')], required=True, default='category')

    category_ids = fields.Many2many('product.category')
    commit_ids = fields.Many2many('commitment.order')
    partner_ids = fields.Many2many('res.partner', string='Customers')


