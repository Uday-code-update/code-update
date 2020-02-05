# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class PriceListForm(models.Model):
    _name = "price.list"

    commitment_date = fields.Date(string='Commitment Date', default=datetime.today())
    box_price = fields.Float(string="Box Price")
    commit_price = fields.Float(string="Commit Price")
    commitment_category = fields.Char(String='Commitment Category')

class CommitCategory(models.Model):
    _name = "commit.category"

    commit_seq = fields.Char(string="Sequence", readonly=True, required=True)

    @api.model
    def create(self, vals):
        if vals.get('commit_seq', 'New') == 'New':
            vals['commit_seq'] = self.env['ir.sequence'].next_by_code(
                'commit.category') or 'New'
        result = super(CommitCategory, self).create(vals)
        return result