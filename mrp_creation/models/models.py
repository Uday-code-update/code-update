# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class MrpCreation(models.Model):
	_name = 'product.mrp_creation'

	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('product.mrp_creation') or 'New'
		result = super(MrpCreation, self).create(vals)       
		return result

	
	@api.multi
	def get_products(self):
		# price = (line.product_id.weight * commit_price) + line.product_id.packing_cost
		data={}
		product_line=[]
		products = self.env['product.template'].search([])
		for product in products:
			list1=[x.product_id.name for x in product.tagged_product_line_ids]
			if len(list1)==2:
				product_line.append((0, 0, {'product':product.id,
										'tag1_product':list1[0],
										'tag2_product': list1[1]}))
			if len(list1)==1:
				product_line.append((0, 0, {'product':product.id,
										'tag1_product':list1[0]}))

			if len(list1)==0:
				pass
		return product_line

	@api.onchange('price_list')
	def get_product_price(self):
		if self.price_list:
			for x in self.price_list.link_categeries_lines_ids:
				for y in self.mrp_details_line_ids:
					if x.commitment_category.id == y.product.categ_id.id:
						y.product_price = (y.product.weight * x.commit_price )+ y.product.packing_cost 



	@api.multi
	def button_update(self):
		res = self.env['ir.actions.act_window'].for_xml_id('mrp_creation', 
				'data_update_action_window')

		res['context'] = {'default_mrp_creation_number':self.name,
				'default_update_ids':[(0,0,{'product':line.product.id,
					'tag1_product':line.tag1_product,
					'tag1_product_mrp':line.tag1_product_mrp,
					'tag2_product':(line.tag2_product),
					'tag2_product_mrp':line.tag2_product_mrp,
					'product_price':line.product_price,
					'mrp':line.mrp
					}) for line in self.mrp_details_line_ids]}
		return res

	name = fields.Char('Name Sequence', required=True, copy=False, 
		readonly=True, index=True, default=lambda self: _('New'))
	user_created = fields.Many2one('res.users',string="User Created")
	date_of_update = fields.Date(string="Date of Update", default=datetime.now())
	price_list = fields.Many2one('product.pricelist',string="Product Pricelist")

	mrp_details_line_ids = fields.One2many('product.mrp_details_line','mrp_details_id',
		string="Line Ids", default=get_products)

	user_update_line_ids = fields.One2many('mrp_details.user_update','user_update_id',
		string="User Update Line Ids")

class MrpDetailsLine(models.Model):
	_name = 'product.mrp_details_line'


	mrp_details_id = fields.Many2one('product.mrp_creation',string="Line ID")
	product = fields.Many2one('product.template',string="Product")
	tag1_product = fields.Char(string="Tag1 Product", readonly=True)
	tag1_product_mrp = fields.Integer(string="Tag1 Product MRP", required=True)
	tag2_product = fields.Char(string="Tag2 Product", readonly=True)
	tag2_product_mrp = fields.Integer(string="Tag2 Product MRP",required=True)
	product_price = fields.Integer(string="Product Price", readonly=True)
	mrp = fields.Integer(string="MRP", required=True)

	update_id = fields.Many2one('mrp_creation.update',string="Update ID")
	tag1_product_new_mrp = fields.Integer(string="Tag1 Product New MRP")
	tag2_product_new_mrp = fields.Integer(string="Tag2 Product New MRP")
	new_mrp = fields.Integer(string="New MRP")


class UserUpdateDetails(models.Model):
	_name = 'mrp_details.user_update'

	user_update_id = fields.Many2one('product.mrp_creation',string="User Update Line Id")
	user = fields.Many2one('res.users',string="User")
	updated_date = fields.Date(string="Updated Date")
	tag1_product = fields.Char(string="Tag1 Product")
	tag1_product_old_mrp = fields.Integer(string="Tag1 Product Old MRP")
	tag1_product_new_mrp = fields.Integer(string="Tag1 Product New MRP")
	tag2_product = fields.Char(string="Tag2 Product")
	tag2_product_old_mrp = fields.Integer(string="Tag2 Product Old MRP")
	tag2_product_new_mrp = fields.Integer(string="Tag2 Product New MRP")
	product_price = fields.Integer(string="Product Price")
	old_mrp = fields.Integer(string="Old MRP")
	new_mrp = fields.Integer(string="New MRP")