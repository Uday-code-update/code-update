# -*- coding: utf-8 -*-

from datetime import datetime,date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp

class mrp(models.Model):
	_inherit = 'mrp.workorder'


	qty_production1 = fields.Float('Original Production Quantity')


	def _generate_lot_ids(self):
		""" Generate stock move lines """
		self.ensure_one()
		MoveLine = self.env['stock.move.line']
		tracked_moves = self.move_raw_ids.filtered(
			lambda move: move.state not in ('done', 'cancel') and move.product_id.tracking != 'none' and move.product_id != self.production_id.product_id and move.bom_line_id)
		for move in tracked_moves:
			qty = move.unit_factor * self.qty_produced
			if move.product_id.tracking == 'serial':
				while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
					MoveLine.create({
						'move_id': move.id,
						'product_uom_qty': 0,
						'product_uom_id': move.product_uom.id,
						'qty_done': min(1, qty),
						'production_id': self.production_id.id,
						'workorder_id': self.id,
						'product_id': move.product_id.id,
						'done_wo': False,
						'location_id': move.location_id.id,
						'location_dest_id': move.location_dest_id.id,
					})
					qty -= 1
			else:
				MoveLine.create({
					'move_id': move.id,
					'product_uom_qty': 0,
					'product_uom_id': move.product_uom.id,
					'qty_done': qty,
					'product_id': move.product_id.id,
					'production_id': self.production_id.id,
					'workorder_id': self.id,
					'done_wo': False,
					'location_id': move.location_id.id,
					'location_dest_id': move.location_dest_id.id,
					})

	@api.multi
	def record_production(self):
		self.ensure_one()
		if self.qty_producing <= 0:
			raise UserError(_('Please set the quantity you are currently producing. It should be different from zero.'))

		if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id and self.move_raw_ids:
			raise UserError(_('You should provide a lot/serial number for the final product'))

		# Update quantities done on each raw material line
		# For each untracked component without any 'temporary' move lines,
		# (the new workorder tablet view allows registering consumed quantities for untracked components)
		# we assume that only the theoretical quantity was used
		for move in self.move_raw_ids:
			if move.has_tracking == 'none' and (move.state not in ('done', 'cancel')) and move.bom_line_id\
						and move.unit_factor and not move.move_line_ids.filtered(lambda ml: not ml.done_wo):
				rounding = move.product_uom.rounding
				if self.product_id.tracking != 'none':
					qty_to_add = float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
					move._generate_consumed_move_line(qty_to_add, self.final_lot_id)
				elif len(move._get_move_lines()) < 2:
					move.quantity_done += float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
				else:
					move._set_quantity_done(move.quantity_done + float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding))

		# Transfer quantities from temporary to final move lots or make them final
		for move_line in self.active_move_line_ids:
			# Check if move_line already exists
			if move_line.qty_done <= 0:  # rounding...
				move_line.sudo().unlink()
				continue
			if move_line.product_id.tracking != 'none' and not move_line.lot_id:
				raise UserError(_('You should provide a lot/serial number for a component'))
			# Search other move_line where it could be added:
			lots = self.move_line_ids.filtered(lambda x: (x.lot_id.id == move_line.lot_id.id) and (not x.lot_produced_id) and (not x.done_move) and (x.product_id == move_line.product_id))
			if lots:
				lots[0].qty_done += move_line.qty_done
				lots[0].lot_produced_id = self.final_lot_id.id
				move_line.sudo().unlink()
			else:
				move_line.lot_produced_id = self.final_lot_id.id
				move_line.done_wo = True

		# One a piece is produced, you can launch the next work order
		if self.next_work_order_id.state == 'pending':
			self.next_work_order_id.state = 'ready'

		self.move_line_ids.filtered(
			lambda move_line: not move_line.done_move and not move_line.lot_produced_id and move_line.qty_done > 0
		).write({
			'lot_produced_id': self.final_lot_id.id,
			'lot_produced_qty': self.qty_producing
		})

		# If last work order, then post lots used
		# TODO: should be same as checking if for every workorder something has been done?
		if not self.next_work_order_id:
			production_move = self.production_id.move_finished_ids.filtered(
								lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
			if production_move.product_id.tracking != 'none':
				move_line = production_move.move_line_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
				if move_line:
					move_line.product_uom_qty += self.qty_producing
					move_line.qty_done += self.qty_production1
				else:
					location_dest_id = production_move.location_dest_id.get_putaway_strategy(self.product_id).id or production_move.location_dest_id.id
					move_line.create({'move_id': production_move.id,
							 'product_id': production_move.product_id.id,
							 'lot_id': self.final_lot_id.id,
							 'product_uom_qty': self.qty_producing,
							 'product_uom_id': production_move.product_uom.id,
							 'qty_done': self.qty_production1,
							 'workorder_id': self.id,
							 'location_id': production_move.location_id.id,
							 'location_dest_id': location_dest_id,
					})
			else:
				production_move.quantity_done += self.qty_producing

		if not self.next_work_order_id:
			for by_product_move in self.production_id.move_finished_ids.filtered(lambda x: (x.product_id.id != self.production_id.product_id.id) and (x.state not in ('done', 'cancel'))):
				if by_product_move.has_tracking != 'serial':
					values = self._get_byproduct_move_line(by_product_move, self.qty_producing * by_product_move.unit_factor)
					self.env['stock.move.line'].create(values)
				elif by_product_move.has_tracking == 'serial':
					qty_todo = by_product_move.product_uom._compute_quantity(self.qty_producing * by_product_move.unit_factor, by_product_move.product_id.uom_id)
					for i in range(0, int(float_round(qty_todo, precision_digits=0))):
						values = self._get_byproduct_move_line(by_product_move, 1)
						self.env['stock.move.line'].create(values)

		# Update workorder quantity produced
		self.qty_produced = self.qty_production1

		if self.final_lot_id:
			self.final_lot_id.use_next_on_work_order_id = self.next_work_order_id
			self.final_lot_id = False

		# Set a qty producing
		rounding = self.production_id.product_uom_id.rounding
		if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
			self.qty_producing = 0
		elif self.production_id.product_id.tracking == 'serial':
			self._assign_default_final_lot_id()
			self.qty_producing = 1.0
			self._generate_lot_ids()
		else:
			self.qty_producing = float_round(self.production_id.product_qty - self.qty_produced, precision_rounding=rounding)
			self._generate_lot_ids()

		if self.next_work_order_id and self.production_id.product_id.tracking != 'none':
			self.next_work_order_id._assign_default_final_lot_id()

		if self.qty_produced == self.qty_production1:
			self.button_finish()
		# else:
		# 	raise UserError(_("Quantity Not Produced totally or current qty is not zero"))
		return True

	# @api.multi
	# def action_confirm(self):
	# 	if self._get_forbidden_state_confirm() & set(self.mapped('state')):
	# 		raise UserError(_(
	# 			'It is not allowed to confirm an order in the following states: %s) % (', '.join(self._get_forbidden_state_confirm())))
	# 	self._action_confirm()
	# 	if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
	# 		self.action_done()

	# 	for line in self.order_line:
	# 		mos = self.env['mrp.production'].search([('product_id','=',line.product_id.id),
	# 			('state','in',['confirmed','planned','progress'])])
	# 		for mo in mos:
	# 			date_planned = datetime.strptime(mo.date_planned_start,'%Y-%m-%d %H:%M:%S').date()
	# 			print(type(date_planned),type(date.today()),":::::::")
	# 			if date_planned == date.today():
	# 				mo.product_qty += line.product_uom_qty
	# 	return True


class MOCreation(models.Model):
	_inherit  = 'procurement.rule'


	@api.multi
	def _run_manufacture(self, product_id, product_qty, product_uom, location_id, name, origin, values):
		Production = self.env['mrp.production']
		ProductionSudo = Production.sudo().with_context(force_company=values['company_id'].id)
		bom = self._get_matching_bom(product_id, values)
		if not bom:
			msg = _('There is no Bill of Material found for the product %s. Please define a Bill of Material for this product.') % (product_id.display_name,)
			raise UserError(msg)

		# create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
		qty=0.0
		check_mo = Production.search([('product_id','=',product_id.id),('state','in',['confirmed','planned','progress'])])
		for mo in check_mo:
			date_planned = datetime.strptime(mo.date_planned_start,'%Y-%m-%d %H:%M:%S').date()
			if date_planned == date.today():
				mo.product_qty += product_qty
				for line in mo.move_raw_ids:
					line.move_raw_ids.product_uom_qty = bom.bom_line_ids.product_qty*line.product_qty/bom.product_qty
					
					stock = self.env['stock.quant'].search([('product_id','=',product_id.id)])
					for x in stock:
						if x.quantity>0.0:
							if product_qty > x.quantity:
								line.product_qty = line.product_qty+(product_qty - x.quantity)
			else:
				production = ProductionSudo.create(self._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, values, bom))
				origin_production = values.get('move_dest_ids') and values['move_dest_ids'][0].raw_material_production_id or False
				orderpoint = values.get('orderpoint_id')
				if orderpoint:
					
					production.message_post_with_view('mail.message_origin_link',
													  values={'self': production, 'origin': orderpoint},
													  subtype_id=self.env.ref('mail.mt_note').id)
				if origin_production:
					production.message_post_with_view('mail.message_origin_link',
													  values={'self': production, 'origin': origin_production},
													  subtype_id=self.env.ref('mail.mt_note').id)
		if not check_mo:
			production = ProductionSudo.create(self._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, values, bom))
			origin_production = values.get('move_dest_ids') and values['move_dest_ids'][0].raw_material_production_id or False
			orderpoint = values.get('orderpoint_id')
			if orderpoint:
				production.message_post_with_view('mail.message_origin_link',
												  values={'self': production, 'origin': orderpoint},
												  subtype_id=self.env.ref('mail.mt_note').id)
			if origin_production:
				production.message_post_with_view('mail.message_origin_link',
												  values={'self': production, 'origin': origin_production},
												  subtype_id=self.env.ref('mail.mt_note').id)
		return True

	@api.multi
	def _get_matching_bom(self, product_id, values):
		if values.get('bom_id', False):
			return values['bom_id']
		return self.env['mrp.bom'].with_context(
			company_id=values['company_id'].id, force_company=values['company_id'].id
		)._bom_find(product=product_id, picking_type=self.picking_type_id)  # TDE FIXME: context bullshit

	def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, values, bom):
		
		qty=0.0
		stock = self.env['stock.quant'].search([('product_id','=',product_id.id)])
		for x in stock:
			if x.quantity>0.0:
				if product_qty > x.quantity:
					qty = product_qty - x.quantity
					return {
						'origin': origin,
						'product_id': product_id.id,
						'product_qty': qty,
						'product_uom_id': product_uom.id,
						'location_src_id': self.location_src_id.id or location_id.id,
						'location_dest_id': location_id.id,
						'bom_id': bom.id,
						'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
						'date_planned_finished': values['date_planned'],
						'procurement_group_id': values.get('group_id').id if values.get('group_id', False) else False,
						'propagate': self.propagate,
						'picking_type_id': self.picking_type_id.id or values['warehouse_id'].manu_type_id.id,
						'company_id': values['company_id'].id,
						'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
					}

		
		return {
			'origin': origin,
			'product_id': product_id.id,
			'product_qty': product_qty,
			'product_uom_id': product_uom.id,
			'location_src_id': self.location_src_id.id or location_id.id,
			'location_dest_id': location_id.id,
			'bom_id': bom.id,
			'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
			'date_planned_finished': values['date_planned'],
			'procurement_group_id': values.get('group_id').id if values.get('group_id', False) else False,
			'propagate': self.propagate,
			'picking_type_id': self.picking_type_id.id or values['warehouse_id'].manu_type_id.id,
			'company_id': values['company_id'].id,
			'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
		}

	def _get_date_planned(self, product_id, values):
		format_date_planned = fields.Datetime.from_string(values['date_planned'])
		date_planned = format_date_planned - relativedelta(days=product_id.produce_delay or 0.0)
		date_planned = date_planned - relativedelta(days=values['company_id'].manufacturing_lead)
		return date_planned
