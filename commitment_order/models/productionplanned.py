# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class ProductionPlanned(models.Model):
    _name = "production.planned"

    name = fields.Char(string="Sequence No.")
    # user_id = fields.Many2one('res.users',string="Create User",default=lambda self: self.env.user)
    create_date = fields.Date(string="Create Date")
    # update_date = fields.Date(string="Update Date")
    # vechile_no = fields.Char(string="Vechile Number")
    vechile_no = fields.Many2one('fleet.vehicle', 'Vehicle')

    attachment_ids = fields.Many2many('ir.attachment', string='Attachment')

    sale_order_line_ids = fields.One2many('sale.order.details.line', 'planned_id')
    invoice_line_ids = fields.One2many('pp.account.invoice', 'planned_id')

    product_detail_ids = fields.One2many('product.details', 'planned_id')
    vehicle_id = fields.Many2one('production.vechile', 'Vehicle ID')

    sale_order_line_total = fields.Float(compute='compute_sale_order_line_total')

    def report_priniting_func(self):
        if self.sale_order_line_ids:
            self.product_detail_ids = []
            for sale in self.sale_order_line_ids:
                for line in sale.sale_id.order_line:
                    self.product_detail_ids = [(0, 0, {
                        "product_name_id": line.product_id.id,
                        "qty": line.product_uom_qty,
                        "delivery_qty": line.qty_delivered,
                        "delivery_id": sale.sale_id.picking_ids and sale.sale_id.picking_ids[0].id
                    })]
        # if self.sale_order_line_ids:
            self.delivery_order_ids = []
            for sale in self.sale_order_line_ids:
                for line in sale.sale_id.picking_ids:
                    self.delivery_order_ids = [(0, 0, {
                        "delivery_id": line.id
                    })]
        # if self.sale_order_line_ids:
            self.invoice_line_ids = []
            for sale in self.sale_order_line_ids:
                for line in sale.sale_id.invoice_ids:
                    self.invoice_line_ids = [(0, 0, {
                        "invoice_id": line.id
                    })]

    def Validate_invoice(self):
        for rec in self:
            for sale in rec.sale_order_line_ids:
                for inv in sale.sale_id.invoice_ids:
                    if inv.state == 'draft':
                        inv = inv.with_context(type='out_invoice', journal_type='sale')
                        inv.action_invoice_open()


    def Product_Details(self):
        for line in self.product_detail_ids:
            line.unlink()
        if self.sale_order_line_ids:
            # self.product_detail_ids = []

            product_detail_ids = []
            for sale in self.sale_order_line_ids:
                for line in sale.sale_id.order_line:
                    product_detail_ids.append({
                        "product_name_id": line.product_id.id,
                        "qty": line.product_uom_qty,
                        "delivery_qty": line.qty_delivered,
                        "delivery_id": sale.sale_id.picking_ids and sale.sale_id.picking_ids[0].id
                    })
            new_product_detail_ids = list({v['delivery_id']:v for v in product_detail_ids}.values())
            st_new_pd = []

            new_data = []

            for x in new_product_detail_ids:
                qty = 0
                delivery_qty = 0
                new_product_detail_ids = []
                for y in product_detail_ids:
                    if x['delivery_id'] == y['delivery_id']:
                        new_product_detail_ids.append(y)
                new_data.append({'delivery_id': x['delivery_id'],
                                 'product_detail_ids': new_product_detail_ids})

            for x in new_data:
                temp_product_detail_ids = list({v['product_name_id']: v for v in x['product_detail_ids']}.values())

                for y in temp_product_detail_ids:
                    qty = 0
                    delivery_qty = 0
                    for a in x['product_detail_ids']:
                        if a['product_name_id'] == y['product_name_id']:
                            qty += a['qty']
                            delivery_qty += a['delivery_qty']
                    self.product_detail_ids = [(0, 0, {
                        "product_name_id": y['product_name_id'],
                        "qty": qty,
                        "delivery_qty": delivery_qty,
                        "delivery_id": a['delivery_id']
                    })]




        return {
            'name': 'Product Details',
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': self.env.ref('commitment_order.production_planned_tree11').id,
            'res_model': 'product.details',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.product_detail_ids.ids)],
            # "target": "new"
        }

    def Delivery_Details(self):
        for line in self.delivery_order_ids:
            line.unlink()
        if self.sale_order_line_ids:
            # self.delivery_order_ids = []

            for sale in self.sale_order_line_ids:
                for line in sale.sale_id.picking_ids:
                    if line.state != 'cancel':
                        self.delivery_order_ids = [(0, 0, {
                            "delivery_id": line.id
                        })]

        return {
            'name': 'Delivery Details',
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': self.env.ref('commitment_order.production_planned_tree121').id,
            'res_model': 'delivery.order.stock',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.delivery_order_ids.ids)],
            # "target": "new"
        }

    def Invoice_Details(self):
        for line in self.invoice_line_ids:
            line.unlink()
        if self.sale_order_line_ids:
            # self.invoice_line_ids = []


            for sale in self.sale_order_line_ids:
                for line in sale.sale_id.invoice_ids:
                    self.invoice_line_ids = [(0, 0, {
                        "invoice_id": line.id
                    })]

        return {
            'name': 'Invoice Details',
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': self.env.ref('commitment_order.production_planned_tree131').id,
            'res_model': 'pp.account.invoice',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.invoice_line_ids.ids)],
            # "target": "new"
        }


    def get_data_gate_pass_pdf(self):

        self.Product_Details()
        pp_categ_ids = set([x.product_name_id.categ_id for x in self.product_detail_ids])

        pp_uom_ids = set([x.product_name_id.uom_id for x in self.product_detail_ids])

        uom_categ_ids = []
        for x in pp_uom_ids:
            for y in pp_categ_ids:
                uom_categ_ids.append({'uom_id': x, 'categ_id': y})

        gate_pass_data = []
        for cat in uom_categ_ids:
            categ_id = ""
            categ_id_seq = ""
            # uom_id = uom.name
            qty = 0
            for x in self.product_detail_ids:
                # if uom.id == x.product_name_id.uom_id.id:
                if x.product_name_id.categ_id.id == cat['categ_id'].id and x.product_name_id.uom_id.id == cat['uom_id'].id:
                    categ_id_seq = cat['categ_id'].commit_seq
                    categ_id = cat['categ_id'].name
                    uom_id = x.product_name_id.uom_id.name
                    qty += x.qty
            gate_pass_data.append({
                "categ_id_seq": categ_id_seq,
                "categ_id": categ_id,
                "uom_id": uom_id,
                "qty": qty,
            })
        return gate_pass_data

    def validate_pp_delivery(self):
        for delivery in self.delivery_order_ids:
            delivery_id = delivery.delivery_id

            delivery_id = delivery_id.with_context(active_id=delivery_id.id, active_ids=delivery_id.ids)
            for line in delivery_id.move_line_ids:
                line.state = 'confirmed'
            for line in delivery_id.move_lines:
                line.reserved_availability = line.product_uom_qty
                line.quantity_done = line.product_uom_qty
            delivery_id.button_validate()


    def create_pp_invoice(self):
        for sale_id in self.sale_order_line_ids:
            sale_advance_pymt_inv = self.env['sale.advance.payment.inv'].create({
                "advance_payment_method": 'delivered',
            })
            sale_advance_pymt_inv = sale_advance_pymt_inv.with_context(active_id=sale_id.sale_id.id, active_ids=sale_id.sale_id.ids)
            sale_advance_pymt_inv.create_invoices()

            for inv in sale_id.sale_id.invoice_ids:
                self.invoice_line_ids = [(0, 0, {
                    "invoice_id": inv.id
                })]


    def tfprint_to_PDF(self):
        self.report_priniting_func()
        return self.env['ir.actions.report']._get_report_from_name('custom_reporting.report_saleordercopp').report_action(
            self.id)

    def tfprint_to_XLSX(self):
        self.report_priniting_func()
        return self.env['ir.actions.report']._get_report_from_name('custom_reporting.ppvcommitment_order_xlsx').report_action(
            self.id)


    def create_gate_pass(self):
        return self.env['ir.actions.report']._get_report_from_name('custom_reporting.gate_pass_report').report_action(
            self.id)

    def get_pp_data1(self):
        html_data = "<table style=\"border: 1px solid black;width: 100%\"><tr><td colspan=\"5\">Delivery Report<td></tr>"
        for line in self.sale_order_line_ids:
            html_data += "<tr><td>Customer Name</td>"
            html_data += "<td>"+line.sale_id.partner_id.name+"</td><td/><td>Commitment Order No</td>"


            co_no = ""
            for ln in line.sale_id.order_line:
                co_no += (ln.commit_id.name or '') + " , "

            html_data += "<td>"+co_no+"</td></tr><tr><td/><td/><td/><td>Sale Order No</td><td>"+line.sale_id.name+"</td><tr/>"

            city = line.sale_id.partner_id.city or ''
            html_data += "<tr><td>City</td><td>"+city+"</td><td/><td>Delivery Order No</td>"



            pi_no = ""
            for ln in line.sale_id.picking_ids:
                pi_no += ln.name + " , "

            html_data += "<td>"+pi_no+"</td></tr><tr/><tr><td colspan=\"3\">Product Detail Report</td><td/><td/><tr/>"

            html_data += "<tr><td>Sr No.</td><td>Product</td><td>Qty</td><td/><td/><tr/>"



            total_qty = 0


            total_qty = 0
            delivery_detail = []
            for sn in line.sale_id.order_line:
                delivery_detail.append({
                    "name": self.name,
                    "product_name": sn.product_id.name,
                    "qty": sn.product_uom_qty,
                })
            set_delivery_detail = []
            if delivery_detail:
                set_delivery_detail = list({v['product_name']: v for v in delivery_detail}.values())
            for stdl in set_delivery_detail:
                temp_qty = 0
                for ln in delivery_detail:
                    if stdl['product_name'] == ln['product_name']:
                        temp_qty+=ln['qty']
                        total_qty+=ln['qty']


                html_data += "<tr>"

                html_data += "<td>" + stdl['name'] + "</td>"
                html_data += "<td>" + stdl['product_name'] + "</td>"
                html_data += "<td>" + str(temp_qty) + "</td>"

                html_data += "<td/><td/></tr>"
                # total_qty += temp_qty




            html_data += "<tr><td/><td>Total</td/><td>"+str(total_qty)+"</td><td/><td/></tr>"

        return "</table>"+html_data


    @api.depends('sale_order_line_ids')
    def compute_sale_order_line_total(self):
        total = sum(operation.total_qty for operation in self.sale_order_line_ids)
        self.sale_order_line_total = total

    product_detail_total = fields.Float(compute='compute_product_detail_total')

    @api.depends('product_detail_ids')
    def compute_product_detail_total(self):
        total = sum(operation.qty for operation in self.product_detail_ids)

        # for line in self.product_detail_ids:
        #     qty = sum([ml.product_qty for ml in line.delivery_id.move_lines if ml.product_id.id == line.product_name_id.id and ml.picking_id.state == 'confirmed'])
        #     line.delivery_qty = qty
        self.product_detail_total = total

    delivery_order_ids = fields.One2many('delivery.order.stock', 'planned_id')

    delivery_order_total = fields.Float(compute='compute_delivery_detail_total')

    @api.depends('delivery_order_ids')
    def compute_delivery_detail_total(self):
        total = sum(operation.total_done for operation in self.delivery_order_ids)
        self.delivery_order_total = total


    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('production.planning.sequence') or '0'
        record = super(ProductionPlanned, self).create(values)
        # record['create_date'] = datetime.today()
        return record

    @api.multi
    def write(self, values):
        # values['update_date'] = datetime.today()
        record = super(ProductionPlanned, self).write(values)
        return record

class SaleOrderDetails(models.Model):
    _name = "sale.order.details.line"

    planned_id = fields.Many2one('production.planned')
    sale_order_no = fields.Char(string="Sale Order No.")
    partner_id = fields.Many2one('res.partner', string="Customer Name",
                                 domain=[('company_type', '=', 'customer')])
    sale_id = fields.Many2one('sale.order')
    city = fields.Char(string="City")
    total_qty = fields.Float(string="Total Qty.", compute='compute_sale_id')

    @api.depends('sale_id')
    def compute_sale_id(self):
        for rec in self:
            rec.total_qty = sum(x.product_uom_qty for x in rec.sale_id.order_line)

class ProductDetails(models.Model):
    _name = "product.details"

    planned_id = fields.Many2one('production.planned')
    product_name_id = fields.Many2one('product.product', string="Product Name")
    qty = fields.Integer(string="Qty")
    delivery_qty = fields.Integer(string="Delivery Qty")
    delivery_id = fields.Many2one('stock.picking')

class DeliveryOrder(models.Model):
    _name = "delivery.order.stock"

    planned_id = fields.Many2one('production.planned')
    delivery_id = fields.Many2one('stock.picking')

    partner_id = fields.Many2one('res.partner', 'Customer Name', related='delivery_id.partner_id')
    city = fields.Char('City', related='delivery_id.partner_id.city')
    total_demanded = fields.Float('Total Demanded', compute='compute_total')
    total_done = fields.Float('Total Done', compute='compute_total')

    @api.depends('total_demanded', 'total_done')
    def compute_total(self):
        for rec in self:
            rec.total_demanded = sum(x.product_uom_qty for x in rec.delivery_id.move_lines)
            rec.total_done = sum(x.quantity_done for x in rec.delivery_id.move_lines)

    # product_name_id = fields.Many2one('product.product', string="Product Name")
    # qty = fields.Integer(string="Qty")

class PPAccountInvoice(models.Model):
    _name = "pp.account.invoice"

    planned_id = fields.Many2one('production.planned')

    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    partner_id = fields.Many2one('res.partner', 'Customer Name', related='invoice_id.partner_id')
    city = fields.Char('City', related='invoice_id.partner_id.city')
    total_qty = fields.Float('Total Qty', compute='compute_invoice_line_details')
    total_amount_tax = fields.Float('Total Amount Tax', compute='compute_invoice_line_details')
    total_amount_total = fields.Float('Total Amount', compute='compute_invoice_line_details')
    total_amount_untaxed = fields.Float('Total Amount Untaxed', compute='compute_invoice_line_details')
    total_amount_residual = fields.Float('Total Amount Due', compute='compute_invoice_line_details')

    def compute_invoice_line_details(self):
        for rec in self:
            if rec.invoice_id:
                rec.total_qty = sum(x.quantity for x in rec.invoice_id.invoice_line_ids)
                rec.total_amount_tax = rec.invoice_id.amount_tax
                rec.total_amount_total = rec.invoice_id.amount_total
                rec.total_amount_untaxed = rec.invoice_id.amount_untaxed
                rec.total_amount_residual = rec.invoice_id.residual