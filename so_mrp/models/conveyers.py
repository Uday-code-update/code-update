# -*- coding: utf-8 -*-

from collections import defaultdict
import math

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare

class Conveyers(models.Model):
	_inherit = 'mrp.production'


	def _workorders_create(self, bom, bom_data):
		"""
		:param bom: in case of recursive boms: we could create work orders for child
					BoMs
		"""
		workorders = self.env['mrp.workorder']
		bom_qty = bom_data['qty']

		# Initial qty producing
		if self.product_id.tracking == 'serial':
			quantity = 1.0
		else:
			quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
			quantity = quantity if (quantity > 0) else 0

		for operation in bom.routing_id.operation_ids:
			# create workorder
			cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
			duration_expected = (operation.workcenter_id.time_start +
								 operation.workcenter_id.time_stop +
								 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
			workorder = workorders.create({
				'name': operation.name,
				'production_id': self.id,
				'workcenter_id': operation.workcenter_id.id,
				'operation_id': operation.id,
				'duration_expected': duration_expected,
				'state': 'ready',
				'qty_producing': quantity,
				'capacity': operation.workcenter_id.capacity,
			})
			if workorders:
				workorders[-1].next_work_order_id = workorder.id
			workorders += workorder

			# assign moves; last operation receive all unassigned moves (which case ?)
			moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
			if len(workorders) == len(bom.routing_id.operation_ids):
				moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
			moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
			moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
			(moves_finished + moves_raw).write({'workorder_id': workorder.id})

			workorder._generate_lot_ids()
		return workorders


	@api.multi
	def button_mark_done(self):
		self.ensure_one()
		total_qty =0.0
		for wo in self.workorder_ids:
			if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
				raise UserError(_('Work order %s is still running') % wo.name)
			total_qty += wo.qty_produced
			if total_qty<self.product_qty:
				raise UserError(_('Total qty is not produced yet'))
		self.post_inventory()
		moves_to_cancel = (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel'))
		moves_to_cancel._action_cancel()
		self.write({'state': 'done', 'date_finished': fields.Datetime.now()})
		return self.write({'state': 'done'})

# class MrpBomOperation(models.Model):
# 	_inherit = 'mrp.bom'


# 	new_operation_id = fields.Many2many('mrp.routing.workcenter',string= 'Consumed in Operation',
# 		help="The operation where the components are consumed, or the finished products created.")

