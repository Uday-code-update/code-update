# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,date

class mrp(models.Model):
	_inherit = 'sale.order'

	@api.multi
	def action_confirm(self):
		if self._get_forbidden_state_confirm() & set(self.mapped('state')):
			raise UserError(_(
				'It is not allowed to confirm an order in the following states: %s'
			) % (', '.join(self._get_forbidden_state_confirm())))
		self._action_confirm()
		if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
			self.action_done()

		for line in self.order_line:
			mos = self.env['mrp.production'].search([('product_id','=',line.product_id.id),
				('state','in',['confirmed','planned','progress'])])
			for mo in mos:
				date_planned = datetime.strptime(mo.date_planned_start,'%Y-%m-%d %H:%M:%S').date()
				print(type(date_planned),type(date.today()),":::::::")
				if date_planned == date.today():
					print(":::::::::::::::::::::::;;;;")
					mo.product_qty += line.product_uom_qty
		return True