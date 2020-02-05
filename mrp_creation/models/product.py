# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Product(models.Model):
	_inherit = 'product.template'

	tagged_product_line_ids = fields.One2many('product.tagged_product','tagged_product_line_id',
		string="Productl Line Ids")

class TaggedProduct(models.Model):
	_name = 'product.tagged_product'

	tagged_product_line_id = fields.Many2one('product.template',string="Line Id")
	product_id = fields.Many2one('product.template',string="Product")