# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductionVechile(models.Model):
    _name = "production.vechile"

    name = fields.Char(string="Production Vechile")
    production_no = fields.Char(string="Production No.")
    user_id = fields.Many2one('res.users', string="Create User", default=lambda self: self.env.user)
    create_date = fields.Date(string="Create Date")
    # update_date = fields.Date(string="Update Date")