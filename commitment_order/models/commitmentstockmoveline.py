# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CommitmentStockMove(models.Model):
    _name = "commitment.stock.move"

    name = fields.Char(string="Name")
    purchase_id = fields.Many2one("purchase.order")
    commitment_id = fields.Many2one("commitment.order")
    line_ids = fields.One2many("commitment.stock.move.line","move_id")
    state = fields.Selection([("cancel","Cancel"),("draft","Draft"),("done","Done")])


class CommitmentStockMoveLine(models.Model):
    _name = "commitment.stock.move.line"

    name = fields.Char(string="Name")
    product_id = fields.Many2one("product.product")
    category_id = fields.Many2one('product.category')
    purchase_id = fields.Many2one("purchase.order")
    commitment_id = fields.Many2one("commitment.order")
    partner_id = fields.Many2one('res.partner')
    move_id = fields.Many2one("commitment.stock.move")
    state = fields.Selection([("cancel","Cancel"),("draft","Draft"),("done","Done")])
    source_location = fields.Many2one("stock.location")
    destination_location = fields.Many2one("stock.location")
    qty = fields.Float('Quantity')





