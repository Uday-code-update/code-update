# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class Producttempladteinherit(models.Model):
    _inherit = "product.template"

    commitment_ok = fields.Boolean(string="Commitment Order")
    product_sequence = fields.Char('Product Sequence')
    packing_cost = fields.Float('Packing Cost')

    @api.model
    def create(self, values):
        if not values.get('commitment_ok') and values.get('sale_ok') or values.get('purchase_ok'):
            values['product_sequence'] = self.env['ir.sequence'].next_by_code('product.product.commit.seq') or '0'
        result = super(Producttempladteinherit, self).create(values)
        return result

    @api.multi
    def write(self, values):
        if not values.get('commitment_ok') and self.product_sequence and values.get('sale_ok') or values.get('purchase_ok'):
            values['product_sequence'] = self.env['ir.sequence'].next_by_code('product.product.commit.seq') or '0'
        record = super(Producttempladteinherit, self).write(values)
        return record

class Producttemplateinherit(models.Model):
    _inherit = "product.pricelist"

    commitment_date = fields.Date(string='Commitment Date')
    link_categeries_lines_ids = fields.One2many('table.filled', 'link_categeries_id', default=lambda self:self.populate_commitment_category())

    def populate_commitment_category(self):
        categ_ids = self.env['product.category'].search([('is_commit', '=', True)], order='commit_seq desc')
        link_categ = []
        for cat in categ_ids:
            link_categ.append((0, 0, {
                'commitment_category': cat.id,
                'box_price': 0,
                'commit_price': 0,
            }))
        return link_categ

    @api.model
    def create(self, values):
        record = super(Producttemplateinherit, self).create(values)
        record['commitment_date'] = datetime.today()
        return record


class TableFilled(models.Model):
    _name = "table.filled"

    link_categeries_id = fields.Many2one("product.pricelist")
    commitment_category = fields.Many2one("product.category", string="Commitment Category", domain=[('is_commit','=','True')])
    box_price = fields.Float(string="Box Price")
    commit_price = fields.Float(string="Commit Price")

#modification to category form
class ProductCategoryInherit(models.Model):
    _inherit = "product.category"

    linked_lines_ids = fields.One2many('link.categories.lines', 'link_categeries_id')
    is_commit = fields.Boolean(string="Commitment Category")
    commit_seq = fields.Char(string="Sequence")
    detecting_stock = fields.Float('Detecting Stock')
    stock_qty = fields.Float('Stock', compute='compute_commitment_stock')

    @api.depends('stock_qty')
    def compute_commitment_stock(self):
        for rec in self:
            line_ids = self.env['commitment.stock.move.line'].search([('category_id', '=', rec.id)])
            rec.stock_qty = sum([x.qty for x in line_ids])

    def CommitmentStockMove(self):
        print("jjjjjjjjjjjjjjjjj")
        return {
            'name': 'Commitment Stock line',
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'view_id': self.env.ref('commitment_order.commitment_stock_move_line_tree').id,
            'res_model': 'commitment.stock.move.line',
            'type': 'ir.actions.act_window',
            "domain": [('id', 'in', self.env['commitment.stock.move.line'].search([('category_id', '=', self.id)]).ids)],
            # "target": "blank"
        }

    @api.model
    def create(self, values):
        if values.get('is_commit'):
            values['commit_seq'] = self.env['ir.sequence'].next_by_code('product.category.commit.seq') or '0'
        # if values['is_commit']:
        #     if values.get('commit_seq', 'New') == 'New':
        #         values['commit_seq'] = self.env['ir.sequence'].next_by_code(
        #             'commit.category') or 'New'
        result = super(ProductCategoryInherit, self).create(values)
        return result

    @api.multi
    def write(self, values):
        if values.get('is_commit') and not self.commit_seq:
            values['commit_seq'] = self.env['ir.sequence'].next_by_code('product.category.commit.seq') or '0'
        record = super(ProductCategoryInherit, self).write(values)
        return record

# this has one2many realtion with product.template(product form)
class LinkCategoriesLines(models.Model):
    _name = "link.categories.lines"

    link_categeries_id = fields.Many2one("product.category")
    internal_category = fields.Many2one("product.category", string="Internal Category", domain=[('is_commit','=','True')])
    fixed_per = fields.Float(string="Fixed Percentage")




class Partnerinherit(models.Model):
    _inherit = "res.partner"

    customer_agent_type = fields.Selection([('customer', 'Customer'), ('agent', 'Agent')])
    # agent_id = fields.Many2one('res.users', 'Agent')

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        move_line = []
        for line in self.order_line:
            if line.product_id.categ_id.is_commit:
                move_line.append((0, 0, {
                    "name": line.product_id.name,
                    "product_id": line.product_id.id,
                    "state": "done",
                    "category_id": line.product_id.categ_id.id,
                    "qty": line.product_qty,
                    # "source_location":
                    # "destination_location":
                    "purchase_id": self.id,
                    "partner_id": self.partner_id.id,
                }))
        if move_line:
            move_id = self.env['commitment.stock.move'].create({
                "name": self.name,
                "purchase_id": self.id,
                "line_ids": move_line,
                "state": "done",
            })
        return res

class SaleOrder(models.Model):
    _inherit = "sale.order"

    production_id = fields.Many2one('production.vechile', 'Production Vehicle')

    ppv_line_id = fields.Many2one('sale.order.details.line')

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get('production_id') and self.state == 'sale':
            planned_id = self.env['production.planned'].search([('vehicle_id', '=', self.production_id.id),
                                                                ('create_date', '=', str(datetime.now().date()))])

            if not planned_id:
                planned_id = planned_id.create({
                    # "sequence_no":
                    # "vechile_no": "4521",
                    "vehicle_id": self.production_id.id
                })

            self.ppv_line_id.planned_id = planned_id.id
        return res

    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()

        for rec in self:
            for so_line in rec.order_line:
                for line in so_line.commit_id.order_line_ids:
                    if so_line.product_id.categ_id.id == line.category_ids.id:
                        line.remaining_qty += so_line.product_uom_qty
                        line.sales_order_qty -= so_line.product_uom_qty
                        line.booked_qty -= so_line.product_uom_qty
                        so_line.commit_id.state = 'order_running'
                for line in so_line.commit_id.sale_line_ids:
                    if line.sale_id.id == rec.id:
                        line.unlink()

        planned_id = self.env['production.planned'].search([('vehicle_id', '=', self.production_id.id),
                                                            ('create_date', '=', str(datetime.now().date()))])
        for line in planned_id.sale_order_line_ids:
            if line.sale_id.id == rec.id:
                line.unlink()

        return res

    # @api.onchange('production_id')
    # def compute_ppv(self):
    #     if self.state == 'sale' and self.production_id:
    #         # if not vehicle_id:
    #         #     vehicle_id = vehicle_id.create({'name': "4521"})
    #         #     self.production_id = vehicle_id.id
    #         #
    #         planned_id = self.env['production.planned'].search([('vehicle_id', '=', self.production_id.id),
    #                                                ('create_date', '=', str(datetime.now().date()))])
    #         total_qty = 0
    #
    #         if not planned_id:
    #             planned_id = planned_id.create({
    #                 # "sequence_no":
    #                 # "vechile_no": "4521",
    #                 "vehicle_id": self.production_id.id
    #             })
    #
    #         self.ppv_line_id.planned_id = planned_id.id

            # for line in self.order_line:
            #     total_qty += line.product_uom_qty
            #     planned_id.product_detail_ids = [(0, 0, {
            #         "product_name_id": line.product_id.id,
            #         "qty": line.product_uom_qty,
            #         "delivery_qty": line.qty_delivered,
            #         "delivery_id": self.picking_ids and self.picking_ids[0].id
            #     })]
            # planned_id.sale_order_line_ids = [(0, 0, {
            #     "sale_order_no": self.name,
            #     "partner_id": self.partner_id.id,
            #     "sale_id": self.id,
            #     "city": self.partner_id.city,
            #     "total_qty": total_qty,
            # })]
            #
            # # Create delivery details in production planned
            # for st in self.picking_ids:
            #     planned_id.delivery_order_ids = [(0, 0, {
            #         'delivery_id': st.id,
            #         # 'product_name_id': line.product_id.id,
            #         # 'qty': line.quantity_done,
            #     })]

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # vehicle_id = self.production_id

        for line in self.order_line:
            if line.commit_id:
                for com in line.commit_id.order_line_ids:
                    if line.product_id.categ_id.id == com.category_ids.id:
                        com.sales_order_qty += line.product_uom_qty

        if self.production_id:
            # if not vehicle_id:
            #     vehicle_id = vehicle_id.create({'name': "4521"})
            #     self.production_id = vehicle_id.id
            #
            planned_id = self.env['production.planned'].search([('vehicle_id', '=', self.production_id.id),
                                                   ('create_date', '=', str(datetime.now().date()))])
            total_qty = 0

            if not planned_id:
                planned_id = planned_id.create({
                    # "sequence_no":
                    # "vechile_no": "4521",
                    "vehicle_id": self.production_id.id
                })

            for line in self.order_line:
                total_qty += line.product_uom_qty
                planned_id.product_detail_ids = [(0, 0, {
                    "product_name_id": line.product_id.id,
                    "qty": line.product_uom_qty,
                    "delivery_qty": line.qty_delivered,
                    "delivery_id": self.picking_ids and self.picking_ids[0].id
                })]
            planned_id.sale_order_line_ids = [(0, 0, {
                "sale_order_no": self.name,
                "partner_id": self.partner_id.id,
                "sale_id": self.id,
                "city": self.partner_id.city,
                "total_qty": total_qty,
            })]

            ppv_line_id = planned_id.sale_order_line_ids.filtered(lambda ppv: ppv.sale_id.id == self.id)
            if ppv_line_id:
                self.ppv_line_id = ppv_line_id[0].id

            # Create delivery details in production planned
            for st in self.picking_ids:
                planned_id.delivery_order_ids = [(0, 0, {
                    'delivery_id': st.id,
                    # 'product_name_id': line.product_id.id,
                    # 'qty': line.quantity_done,
                })]

        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    commit_id = fields.Many2one('commitment.order', 'Commitment Order')

    @api.multi
    def write(self, vals):
        if self.commit_id:
            for line in self.commit_id.order_line_ids:
                if line.category_ids.id == self.product_id.categ_id.id:
                    if vals.get('product_uom_qty'):
                        if self.product_uom_qty > vals.get('product_uom_qty'):
                            qty_dif = self.product_uom_qty - vals.get('product_uom_qty')
                            line.remaining_qty += qty_dif
                        else:
                            qty_dif = vals.get('product_uom_qty') - self.product_uom_qty
                            line.remaining_qty -= qty_dif
                            if line.remaining_qty < 0:
                                raise ValidationError('There is no sufficient stock in commitment order!')
                        self.commit_id.state = 'order_running'
                    line.booked_qty = line.ordered_qty - line.remaining_qty
                    line.sales_order_qty = line.ordered_qty - line.remaining_qty

                    if vals.get('qty_delivered'):
                        if self.qty_delivered > vals.get('qty_delivered'):
                            qty_dif = self.qty_delivered - vals.get('qty_delivered')
                            line.delivery_qty += qty_dif
                        else:
                            qty_dif = vals.get('qty_delivered') - self.qty_delivered
                            line.delivery_qty += qty_dif

        return super(SaleOrderLine, self).write(vals)


# class StockPicking(models.Model):
#     _inherit = "stock.picking"
#
#     def button_validate(self):
#         res = super(StockPicking, self).button_validate()
#         sale_ids = self.env['sale.order'].search([]).filtered(lambda rec: self.id in rec.picking_ids.ids)
#         for sale_id in sale_ids:
#             planned_id = self.env['production.planned'].search([('vehicle_id', '=', sale_id.production_id.id)])
#             for line in self.move_lines:
#                 planned_id.delivery_order_ids = [(0, 0, {
#                     'delivery_id': self.id,
#                     'product_name_id': line.product_id.id,
#                     'qty': line.quantity_done,
#                 })]
#         return res

class UOM(models.Model):
    _inherit = "product.uom"

    uom_seq = fields.Char('UOM Sequence')

    @api.model
    def create(self, values):
        values['uom_seq'] = self.env['ir.sequence'].next_by_code('uom.uom.commit.seq') or '0'
        result = super(UOM, self).create(values)
        return result