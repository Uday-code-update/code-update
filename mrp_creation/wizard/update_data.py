# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class UpdateData(models.Model):
	_name = 'mrp_creation.update'

	@api.multi
	def update(self):
		mrp = self.env['product.mrp_creation'].search([('name','=',self.mrp_creation_number)])
		for x in self.update_ids:
			if x.tag1_product_new_mrp or x.tag2_product_new_mrp or x.new_mrp:
				lines= [(0,0,{'user':self.env.user,
							'updated_date':datetime.now(),
							'tag1_product':x.tag1_product,
							'tag1_product_old_mrp':x.tag1_product_mrp,
							'tag1_product_new_mrp':x.tag1_product_new_mrp,
							'tag2_product':x.tag2_product,
							'tag2_product_old_mrp':x.tag2_product_mrp,
							'tag2_product_new_mrp':x.tag2_product_new_mrp,
							'product_price': x.product_price,
							'old_mrp':x.mrp,
							'new_mrp':x.new_mrp})
							 ]

				mrp.user_update_line_ids = lines
				for y in mrp.mrp_details_line_ids:
					if y.product.id == x.product.id:
						y.tag1_product_mrp = x.tag1_product_new_mrp
						y.tag2_product_mrp = x.tag2_product_new_mrp
						y.mrp = x.new_mrp


	update_ids = fields.One2many('product.mrp_details_line','update_id',
		string="Update IDS")
	mrp_creation_number= fields.Char(string="MRP Creation Number")
	product = fields.Many2one('product.template',string="Product")
	tag1_product = fields.Char(string="Tag1 Product", readonly=True)
	tag1_product_mrp = fields.Integer(string="Tag1 Product MRP")
	tag1_product_new_mrp = fields.Integer(string="Tag1 Product New MRP")
	tag2_product = fields.Char(string="Tag2 Product", readonly=True)
	tag2_product_mrp = fields.Integer(string="Tag2 Product MRP")
	tag2_product_new_mrp = fields.Integer(string="Tag2 Product New MRP")
	product_price = fields.Integer(string="Product Price", readonly=True)
	mrp = fields.Integer(string="MRP", readonly=True)
	new_mrp = fields.Integer(string="New MRP")
	

