# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError, UserError

class Commitmentorder(models.Model):
    _name = "commitment.order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string="Name", default='New')
    partner_id = fields.Many2one('res.partner',string="Customer Name", domain=[('customer_agent_type','=','customer')])

    @api.onchange('partner_id')
    def compute_agent_id(self):
        if self.partner_id:
            self.user_id = self.partner_id.user_id.id

    user_id = fields.Many2one('res.users',string='Agent Name', domain=[('customer_agent_type','=','agent')])
    price_list_id = fields.Many2one('product.pricelist',string="Price List",default=lambda self: self.get_all_comit_category())#, domain=[('company_type','=','agent')])
    expiry_date = fields.Date(string="Expiry Date", default=datetime.now().date()+timedelta(days=7), readonly=True)
    order_line_ids = fields.One2many('commitment.order.line', 'commitment_order_id',
                                     default=lambda self: self.populate_line())



    def preview_commitment_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def total_sale_order(self):
        sale_ids = [x.sale_id.id for x in self.sale_line_ids]
        print("Sale order-------------", sale_ids)
        return {
            'name': 'Sale Order',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('sale.view_quotation_tree').id,
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', sale_ids)]
            # 'res_id': sale_id.id,
            # 'active_ids': sale_ids,
            # 'context': {'default_ids': sale_ids}
            # "target": "new"
        }

    def total_delivery_orders(self):
        picking_ids = [x.sale_id.mapped('picking_ids') for x in self.sale_line_ids]
        picking_ids_r = []
        for x in picking_ids:
            for pick in x:
                picking_ids_r.append(pick.id)
        print("Delivery IDS-------------", picking_ids)
        return {
            'name': 'Delivery Order',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('stock.vpicktree').id,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', picking_ids_r)]
            # 'res_id': sale_id.id,
            # 'active_ids': sale_ids,
            # 'context': {'default_ids': sale_ids}
            # "target": "new"
        }

    def total_invoice_orders(self):
        invoice_ids = [x.sale_id.mapped('invoice_ids') for x in self.sale_line_ids]
        invoice_ids_r = []
        for x in invoice_ids:
            for pick in x:
                invoice_ids_r.append(pick.id)
        print("Invoice IDS-------------", invoice_ids)
        return {
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('account.invoice_tree').id,
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids_r)]
            # 'res_id': sale_id.id,
            # 'active_ids': sale_ids,
            # 'context': {'default_ids': sale_ids}
            # "target": "new"
        }

    @api.constrains('order_line_ids')
    def _check_order_line_ids(self):
        # if not self.order_line_ids:
        #     raise ValidationError(_('Please select Order Book!'))
        quotation_data = ""
        for line in self.order_line_ids:
            if line.ordered_qty <= 0:
                quotation_data += line.category_ids.name + " category\n"
        if quotation_data:
            raise ValidationError(
                _('The quantity should not be zero in order book! Below are the quotation for zero quantities data:\n'+quotation_data))

    state = fields.Selection([('cancel', 'Cancel'), ('draft', 'Draft'), ('commitment_order', 'Commitment Order'),
                              ('order_running', 'Order Running'), ('completed', 'Completed')],
                             default='draft', required=True)

    def cancel_commit_order(self):
        for rec in self:
            for line in rec.order_line_ids:
                for st_ln in line.com_stk_line_ids:
                    st_ln.unlink()
            rec.state = 'cancel'

    sale_line_ids = fields.One2many('commit.sale.order', 'commit_id')


    ordered_qty = fields.Integer(string="Ordered Qty", compute='compute_ordered_booked_remaining_delivery_qty')
    booked_qty = fields.Integer(string="Booked Qty", compute='compute_ordered_booked_remaining_delivery_qty')
    remaining_qty = fields.Integer(string="Remaining Qty", compute='compute_ordered_booked_remaining_delivery_qty')
    delivery_qty = fields.Integer(string="Delivery Qty", compute='compute_ordered_booked_remaining_delivery_qty')


    # sales_order_no = fields.Char(string="Sales Order No.")
    # sale_line_ids = fields.Many2many('sale.order')


    sale_value =fields.Float(string="Sale Value")
    invoice_value = fields.Float(string="Invoice Value")
    due_amount = fields.Float(string="Due Amount")

    @api.depends('ordered_qty', 'booked_qty', 'remaining_qty', 'delivery_qty')
    def compute_ordered_booked_remaining_delivery_qty(self):
        for rec in self:
            rec.ordered_qty = sum([rec.ordered_qty for rec in rec.order_line_ids])
            rec.booked_qty = sum([rec.sales_order_qty for rec in rec.order_line_ids])
            rec.remaining_qty = sum([rec.remaining_qty for rec in rec.order_line_ids])
            rec.delivery_qty = sum([rec.delivery_qty for rec in rec.order_line_ids])

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('commit.sequence') or '0'
        vals['state'] = 'commitment_order'

        res = super(Commitmentorder, self).create(vals)
        move_line = []
        move_id = self.env['commitment.stock.move'].create({
            "name": res.name,
            "commitment_id": res.id,
            # "purchase_id": self.id,
            # "line_ids": move_line,
            "state": "done",
        })
        for line in res.order_line_ids:
            print("line", line)
            for cat_line in line.category_ids.linked_lines_ids:
                print("llllllllllllllllllllllllllllllllllllllllllllllll", cat_line.link_categeries_id.name)


                stkmove_line_id = self.env['commitment.stock.move.line'].create({
                    "name": cat_line.internal_category.name,
                    # "product_id": line.product_id.id,
                    "state": "done",
                    "category_id": cat_line.internal_category.id,
                    "qty": -(line.ordered_qty*line.category_ids.detecting_stock*cat_line.fixed_per/100),
                    # "source_location":
                    # "destination_location":
                    "commitment_id": res.id,
                    # "purchase_id": self.id,
                    "partner_id": res.partner_id.id,
                    "move_id": move_id.id,
                })

                # move_id.line_ids = move_line
                line.com_stk_line_ids = [(4, stkmove_line_id.id)]


        return res

    @api.multi
    def write(self, vals):
        res = super(Commitmentorder, self).write(vals)
        if vals.get('order_line_ids', ''):
            if self.state in ['draft', 'commitment_order']:
                for line in self.order_line_ids:
                    print("line", line)
                    for cat_line in line.category_ids.linked_lines_ids:
                        print("llllllllllllllllllllllllllllllllllllllllllllllll", cat_line.link_categeries_id.name)

                        move_line = self.env['commitment.stock.move.line'].search([('commitment_id', '=', self.id)])
                        move_line.write({
                            "qty": -(line.ordered_qty * line.category_ids.detecting_stock * cat_line.fixed_per / 100),
                        })

        return res

    def confirm_commit_order(self):

        for rec in self:
            if rec.state == 'cancel':
                move_line = []
                move_id = self.env['commitment.stock.move'].create({
                    "name": rec.name,
                    "commitment_id": rec.id,
                    # "purchase_id": self.id,
                    # "line_ids": move_line,
                    "state": "done",
                })
                for line in rec.order_line_ids:
                    print("line", line)
                    for cat_line in line.category_ids.linked_lines_ids:
                        print("llllllllllllllllllllllllllllllllllllllllllllllll", cat_line.link_categeries_id.name)

                        stkmove_line_id = self.env['commitment.stock.move.line'].create({
                            "name": cat_line.internal_category.name,
                            # "product_id": line.product_id.id,
                            "state": "done",
                            "category_id": cat_line.internal_category.id,
                            "qty": -(line.ordered_qty * line.category_ids.detecting_stock * cat_line.fixed_per / 100),
                            # "source_location":
                            # "destination_location":
                            "commitment_id": rec.id,
                            # "purchase_id": self.id,
                            "partner_id": rec.partner_id.id,
                            "move_id": move_id.id,
                        })

                        # move_id.line_ids = move_line
                        line.com_stk_line_ids = [(4, stkmove_line_id.id)]
                rec.state = 'commitment_order'



    def sale_order_form(self):
        if self.state == "completed":
            return
        total_len = len(self.order_line_ids)
        count = 0
        for cat in self.order_line_ids:
            if cat.remaining_qty <= 0:
                count += 1
        if count == total_len:
            raise ValidationError('No Category to create sale order!')
        return {
            'name': 'Sale Order',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('commitment_order.sale_order_popup_form').id,
            'res_model': 'sale.order.transient',
            'type': 'ir.actions.act_window',
            # 'res_id': sale_id.id,
            "target": "new"
        }

    def get_all_comit_category(self):
        # return
        price_list_id = self.env['product.pricelist'].search([], order='commitment_date desc')
        if price_list_id:
            price_list_id = price_list_id.filtered(lambda self:str(self.commitment_date)==str(datetime.now().date()))
            if price_list_id:
                return price_list_id[0].id

    def populate_line(self):
        price_list_id = self.env['product.pricelist'].search([], order='commitment_date desc')
        if price_list_id:
            price_list_id = price_list_id.filtered(lambda self:str(self.commitment_date)==str(datetime.now().date()))
            if price_list_id:
                price_list_id = price_list_id[0]
                order_line_ids = []
                if price_list_id:
                    for cat in price_list_id.link_categeries_lines_ids:
                        order_line_ids.append((0, 0, {
                            "category_ids": cat.commitment_category.id,
                            "ordered_qty": 0,
                            "booked_qty": 0,
                            "remaining_qty": 0,
                            "delivery_qty": 0
                        }))
                return order_line_ids



class Commitmentorderline(models.Model):
    _name = "commitment.order.line"

    commitment_order_id = fields.Many2one("commitment.order")
    category_ids = fields.Many2one('product.category', string="Category", domain=[('is_commit', '=', True)], required=True)

    com_stk_line_ids = fields.Many2many('commitment.stock.move.line')

    @api.onchange('category_ids')
    def onchange_category_ids(self):
        # force domain on task when project is set
        category_ids = self.env['product.category'].search([('is_commit', '=', True)], order='commit_seq')
        for cat in category_ids:
            print(cat.commit_seq, '-------------', cat.id)

        print("kkkkkkkkkkkkkkkkkkkkkkkkkkkkkk", category_ids.ids)

        return {'domain': {
            'category_ids': [('id', 'in', category_ids.ids)]
        }}

    ordered_qty = fields.Integer(string="Ordered Qty", required=True)

    @api.depends('ordered_qty')
    def compute_remaining_qty(self):
        for rec in self:
            if rec.ordered_qty:
                rec.remaining_qty = rec.ordered_qty

    booked_qty = fields.Integer(string="Booked Qty", compute='compute_remaining_qty', store=True)
    remaining_qty = fields.Integer(string="Remaining Qty", compute='compute_remaining_qty', store=True)
    delivery_qty = fields.Integer(string="Delivery Qty", compute='compute_remaining_qty', store=True)
    sales_order_qty = fields.Float('Sales Order qty', compute='compute_remaining_qty', store=True)

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(Commitmentorderline, self).fields_get(fields, attributes)
        # if self.commitment_order_id.state in ['order_running', 'completed']:
        if res.get('booked_qty'):
            res['booked_qty']['readonly'] = True
        if res.get('remaining_qty'):
            res['remaining_qty']['readonly'] = True
        if res.get('delivery_qty'):
            res['delivery_qty']['readonly'] = True
        if res.get('sales_order_qty'):
            res['sales_order_qty']['readonly'] = True

        return res

class CommitSaleOrder(models.Model):
    _name = "commit.sale.order"

    commit_id = fields.Many2one('commitment.order')
    name = fields.Char('Name')
    sale_id = fields.Many2one('sale.order')

    ordered_qty = fields.Integer(string="Ordered Qty")
    booked_qty = fields.Integer(string="Booked Qty", compute='compute_booked_remaining_delivery_qty')
    remaining_qty = fields.Integer(string="Remaining Qty", compute='compute_booked_remaining_delivery_qty')
    delivery_qty = fields.Integer(string="Delivery Qty", compute='compute_booked_remaining_delivery_qty')
    adjusted_qty = fields.Float('Adjusted Quantity')
    adjusted_commitment_order_id = fields.Many2many('commitment.order', string='Adjusted Commitment Order')
    status = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    @api.depends('booked_qty', 'remaining_qty', 'delivery_qty')
    def compute_booked_remaining_delivery_qty(self):
        for rec in self:
            if rec.sale_id:
                print("booked",rec.booked_qty)
                print("delivery",rec.delivery_qty)
                print("remaining",rec.remaining_qty)
                rec.booked_qty = sum([rec.product_uom_qty for rec in rec.sale_id.order_line])
                rec.delivery_qty = sum([rec.qty_delivered for rec in rec.sale_id.order_line])
                rec.remaining_qty = rec.ordered_qty-rec.delivery_qty


class SaleOrderPopup(models.TransientModel):
    _name = "sale.order.transient"

    name = fields.Char('Name')
    line_ids = fields.One2many('sale.order.transient.line', 'sale_id')
    action_commitment = fields.Selection([('auto_create_commitment', 'Auto Create Commitment Order'),
                                               ('merge_commitment_order', 'Merge Order Commitment')])

    def create_sale_order(self):
        if self._context.get('active_id'):
            commit_id = self.env['commitment.order'].browse(int(self._context.get('active_id')))


            quotation_value = ""
            commit_order_line = []
            new_commit_id = self.env['commitment.order']
            new_commit_id_total_qty = 0
            for line in commit_id.order_line_ids:
                qty = sum([x.qty for x in self.line_ids if x.product_id.categ_id.id == line.category_ids.id])
                if qty > line.remaining_qty:
                    quotation_value += "%s category value crosses the limit!\n"%(line.category_ids.name)
                    new_commit_id_total_qty += qty - line.remaining_qty
                    commit_order_line.append((0, 0, {
                        "category_ids": line.category_ids.id,
                        "ordered_qty": qty - line.remaining_qty,
                        "remaining_qty": qty - line.remaining_qty,
                    }))

            commit_ids = self.env['commitment.order']
            if self.action_commitment == 'auto_create_commitment':
                if quotation_value:

                    price_list_id_at = self.env['product.pricelist'].search([], order='commitment_date desc')
                    if price_list_id_at:
                        price_list_id_at = price_list_id_at.filtered(
                            lambda self: str(self.commitment_date) == str(datetime.now().date()))
                        if price_list_id_at:
                            price_list_id_at = price_list_id_at[0]
                        else:
                            raise ValidationError('There is no pricelist for today!')

                    new_commit_id = self.env['commitment.order'].create({
                        'partner_id': commit_id.partner_id.id,
                        'user_id': commit_id.user_id.id,
                        'price_list_id': price_list_id_at.id,
                        'expiry_date': commit_id.expiry_date,
                        'order_line_ids': commit_order_line
                    })
                    new_commit_id.state = "completed"

                if not new_commit_id:
                    raise ValidationError(quotation_value)
            elif self.action_commitment == 'merge_commitment_order':
                commit_ids = commit_ids.search(
                    [('state', 'in', ['commitment_order', 'order_running']),
                     ('id', '!=', commit_id.id),
                     ('partner_id', '=', commit_id.partner_id.id)],
                    order='id ASC')

                merge_order_line = []
                new_commit_ids = commit_ids+commit_id
                for com in new_commit_ids:
                    for com_line in com.order_line_ids:

                        for line in self.line_ids:
                            if line.product_id.categ_id.id == com_line.category_ids.id and line.qty != 0:


                                # Calculate price
                                price_list_id = com.price_list_id.link_categeries_lines_ids
                                commit_price = sum(
                                    [x.commit_price for x in price_list_id if
                                     x.commitment_category.id == line.product_id.categ_id.id])

                                price = (line.product_id.weight * commit_price) + line.product_id.packing_cost
                                price_without_tax = (price / (sum(
                                    [sum([a.amount for a in x.children_tax_ids]) for x in
                                     line.product_id.taxes_id]) + 100)) * 100
                                # end

                                # temp_qty = 0
                                if com_line.remaining_qty >= line.qty:
                                    merge_order_line.append((0, 0, dict(
                                        customer_lead=1,
                                        name=line.product_id.name,
                                        product_id=line.product_id.id,
                                        price_unit=price_without_tax,
                                        product_uom_qty=line.qty,
                                        commit_id=com.id,
                                    )))
                                    # line.qty -= com_line.ordered_qty
                                    com_line.remaining_qty = com_line.remaining_qty - line.qty
                                    line.qty = 0
                                else:
                                    while line.qty>0 and com_line.remaining_qty>0:
                                        if com_line.remaining_qty < line.qty:
                                            merge_order_line.append((0, 0, dict(
                                                customer_lead=1,
                                                name=line.product_id.name,
                                                product_id=line.product_id.id,
                                                price_unit=price_without_tax,
                                                product_uom_qty=com_line.remaining_qty,
                                                commit_id=com.id,
                                            )))
                                            line.qty = line.qty - com_line.remaining_qty
                                            com_line.remaining_qty = 0

                                        # else:
                                        #     merge_order_line.append((0, 0, dict(
                                        #         customer_lead=1,
                                        #         name=line.product_id.name,
                                        #         product_id=line.product_id.id,
                                        #         price_unit=999,
                                        #         product_uom_qty=(com_line.remaining_qty-line.qty) if (com_line.remaining_qty-line.qty)>0 else com_line.remaining_qty,
                                        #         commit_id=com.id,
                                        #     )))
                                        #     line.qty = line.qty-com_line.remaining_qty


                                        # sum([x.qty for x in self.line_ids if x.product_id.categ_id.id == line.category_ids.id])

                for com in commit_ids:
                    for line in com.order_line_ids:
                        if line.remaining_qty == 0:
                            line.booked_qty = line.ordered_qty
                            com.state = 'completed'
                        else:
                            line.booked_qty = line.ordered_qty - line.remaining_qty


            # elif self.action_commitment == 'merge_commitment_order':
            #     commit_ids = commit_ids.search([('state', 'in', ['commitment_order', 'order_running']), ('id', '!=', commit_id.id)], order='id ASC')
            #     for com in commit_ids:
            #         check = True
            #         for line in com.order_line_ids:
            #             for x in commit_order_line:
            #                 print("ooooooooooooooooooooooooooo", x)
            #                 if line.category_ids.id == x[2]['category_ids']:
            #                     temp = x[2]['remaining_qty']
            #                     x[2]['remaining_qty'] = x[2]['remaining_qty'] - line.remaining_qty
            #                     line.remaining_qty = line.remaining_qty - (temp - x[2]['remaining_qty'])
            #                     line.booked_qty = line.ordered_qty - line.remaining_qty
            #             if line.remaining_qty != 0:
            #                 check = False
            #         if check:
            #             com.state = 'completed'

            else:
                if quotation_value:
                    raise ValidationError(quotation_value)


            sale_id = self.env['sale.order']
            sale_id = sale_id.create(dict(
                partner_id=commit_id.partner_id.id,
                partner_invoice_id=commit_id.partner_id.id,
                partner_shipping_id=commit_id.partner_id.id,
                company_id=self.env.user.company_id.id,
                currency_id=self.env.user.company_id.currency_id.id,
                date_order=datetime.now(),
                # name='fg',
                picking_policy='direct',
                pricelist_id=commit_id.price_list_id.id,
                warehouse_id=self.env['stock.warehouse'].search([], limit=1).id
            ))

            total_row_qty = 0


            if self.action_commitment == 'merge_commitment_order':
                sale_id.order_line = merge_order_line
                for mrln in merge_order_line:
                    for cm in commit_ids:
                        if mrln[2]['commit_id'] == cm.id:
                            cm.sale_line_ids = [(0, 0, {
                                'name': sale_id.name,
                                'sale_id': sale_id.id,
                                'ordered_qty': mrln[2]['product_uom_qty'],
                                # 'adjusted_qty': mrln[2]['product_uom_qty'],
                                # 'adjusted_commitment_order_id': [(4, new_commit_id.id)],
                                # 'booked_qty': commit_id,
                                # 'remaining_qty': commit_id,
                                # 'delivery_qty': commit_id,
                            })]
            elif self.action_commitment == 'auto_create_commitment':
                for line in self.line_ids:
                    com_line_id = [x for x in commit_id.order_line_ids if x.category_ids.id == line.product_id.categ_id.id]

                    com_line_id[0].booked_qty += line.qty
                    com_line_id[0].remaining_qty -= line.qty

                    autocom_line_id = [x for x in new_commit_id.order_line_ids if x.category_ids.id == line.product_id.categ_id.id]
                    autocom_line_id[0].booked_qty += autocom_line_id[0].ordered_qty
                    autocom_line_id[0].remaining_qty -= autocom_line_id[0].ordered_qty


                    price_list_id = commit_id.price_list_id.link_categeries_lines_ids
                    commit_price = sum(
                        [x.commit_price for x in price_list_id if x.commitment_category.id == line.product_id.categ_id.id])

                    price = (line.product_id.weight * commit_price) + line.product_id.packing_cost
                    price_without_tax = (price / (sum(
                        [sum([a.amount for a in x.children_tax_ids]) for x in line.product_id.taxes_id]) + 100)) * 100

                    sale_id.order_line = [(0, 0, dict(
                        customer_lead=1,
                        name=line.product_id.name,
                        product_id=line.product_id.id,
                        price_unit=price_without_tax,
                        product_uom_qty=com_line_id[0].ordered_qty,
                        commit_id=commit_id.id,
                    ))]

                    price_list_id = new_commit_id.price_list_id.link_categeries_lines_ids
                    commit_price = sum(
                        [x.commit_price for x in price_list_id if
                         x.commitment_category.id == line.product_id.categ_id.id])

                    price = (line.product_id.weight * commit_price) + line.product_id.packing_cost
                    price_without_tax = (price / (sum(
                        [sum([a.amount for a in x.children_tax_ids]) for x in line.product_id.taxes_id]) + 100)) * 100
                    sale_id.order_line = [(0, 0, dict(
                        customer_lead=1,
                        name=line.product_id.name,
                        product_id=line.product_id.id,
                        price_unit=price_without_tax,
                        product_uom_qty=autocom_line_id[0].ordered_qty,
                        commit_id=new_commit_id.id,
                    ))]
                    total_row_qty += line.qty


            else:
                for line in self.line_ids:
                    com_line_id = [x for x in commit_id.order_line_ids if x.category_ids.id == line.product_id.categ_id.id]

                    com_line_id[0].booked_qty += line.qty
                    com_line_id[0].remaining_qty -= line.qty



                    price_list_id = commit_id.price_list_id.link_categeries_lines_ids
                    commit_price = sum(
                        [x.commit_price for x in price_list_id if x.commitment_category.id == line.product_id.categ_id.id])

                    price = (line.product_id.weight * commit_price) + line.product_id.packing_cost
                    price_without_tax = (price / (sum(
                        [sum([a.amount for a in x.children_tax_ids]) for x in line.product_id.taxes_id]) + 100)) * 100



                    print('kjhkhkjhkjhkhkjhjhkh',line.price_without_tax)
                    sale_id.order_line = [(0, 0, dict(
                        customer_lead=1,
                        name=line.product_id.name,
                        product_id=line.product_id.id,
                        price_unit=price_without_tax,
                        product_uom_qty=line.qty,
                        commit_id=commit_id.id,
                    ))]
                    total_row_qty += line.qty

            if self.action_commitment == 'auto_create_commitment':
                commit_id.sale_line_ids = [(0, 0, {
                    'name': sale_id.name,
                    'sale_id': sale_id.id,
                    'ordered_qty': total_row_qty,
                    'adjusted_qty': new_commit_id_total_qty,
                    'adjusted_commitment_order_id': [(4, new_commit_id.id)],
                    # 'booked_qty': commit_id,
                    # 'remaining_qty': commit_id,
                    # 'delivery_qty': commit_id,
                })]
                new_commit_id.sale_line_ids = [(0, 0, {
                    'name': sale_id.name,
                    'sale_id': sale_id.id,
                    'ordered_qty': new_commit_id_total_qty,
                    # 'adjusted_qty': new_commit_id_total_qty,
                    # 'adjusted_commitment_order_id': new_commit_id.id,
                    # 'booked_qty': commit_id,
                    # 'remaining_qty': commit_id,
                    # 'delivery_qty': commit_id,
                })]
            elif self.action_commitment == 'merge_commitment_order':
                commit_id.sale_line_ids = [(0, 0, {
                    'name': sale_id.name,
                    'sale_id': sale_id.id,
                    'ordered_qty': commit_id.ordered_qty,
                    'adjusted_qty': sum([sum([y.booked_qty for y in x.order_line_ids]) for x in commit_ids]),
                    'adjusted_commitment_order_id': [(6, 0, commit_ids.ids)],
                    # 'booked_qty': commit_id,
                    # 'remaining_qty': commit_id,
                    # 'delivery_qty': commit_id,
                })]
                # new_commit_id.sale_line_ids = [(0, 0, {
                #     'name': sale_id.name,
                #     'sale_id': sale_id.id,
                #     'ordered_qty': new_commit_id_total_qty,
                #     # 'adjusted_qty': new_commit_id_total_qty,
                #     # 'adjusted_commitment_order_id': new_commit_id.id,
                #     # 'booked_qty': commit_id,
                #     # 'remaining_qty': commit_id,
                #     # 'delivery_qty': commit_id,
                # })]
            else:
                commit_id.sale_line_ids = [(0, 0, {
                    'name': sale_id.name,
                    'sale_id': sale_id.id,
                    'ordered_qty': total_row_qty,
                    # 'adjusted_qty': total_row_qty,
                    # 'adjusted_commitment_order_id': [(6, 0, commit_ids.ids)],
                    # 'booked_qty': commit_id,
                    # 'remaining_qty': commit_id,
                    # 'delivery_qty': commit_id,
                })]

            commit_id.state = 'order_running'
            total_len = len(commit_id.order_line_ids)
            count = 0
            for cat in commit_id.order_line_ids:
                cat.booked_qty = cat.ordered_qty-cat.remaining_qty
                if cat.remaining_qty <= 0:
                    count += 1
            if count == total_len:
                commit_id.state = 'completed'





            return {
                # 'name': 'Sale Order',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('sale.view_order_form').id,
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': sale_id.id,
                # "target": "new"
            }

class SaleOrderLineTransient(models.TransientModel):
    _name = "sale.order.transient.line"

    sale_id = fields.Many2one('sale.order.transient')
    product_id = fields.Many2one('product.product')
    category_id = fields.Many2one('product.category', realted='product_id.categ_id')
    qty = fields.Float('Float')
    price = fields.Float()
    total = fields.Float()
    price_without_tax = fields.Float('Without Tax')

    @api.onchange('qty')
    def compute_total(self):
        if self.qty:
            self.total = self.qty * self.price_without_tax

    @api.onchange('qty')
    def add_validation_qty(self):
        pass
        # if self._context.get('active_id'):
        #     commit_id = self.env['commitment.order'].browse(int(self._context.get('active_id')))
        #     print('self.sale_id.line_ids', self.sale_id.line_ids)
        #     for line in commit_id.order_line_ids:
        #         qty = sum([x.qty for x in self.sale_id.line_ids if x.product_id.categ_id.id == line.category_ids.id])
        #         print('qty', self.sale_id.line_ids)
        #         print('quantity', qty)
        #         if qty > line.remaining_qty:
        #             raise ValidationError('Please Enter less quantity!')

    @api.onchange('product_id')
    def compute_category_id(self):
        if self.product_id:
            self.category_id = self.product_id.categ_id.id

            if self._context.get('active_id'):
                commit_id = self.env['commitment.order'].browse(int(self._context.get('active_id')))
                price_list_id = commit_id.price_list_id.link_categeries_lines_ids
                commit_price = sum([x.commit_price for x in price_list_id if x.commitment_category.id == self.product_id.categ_id.id])

                self.price = (self.product_id.weight * commit_price) + self.product_id.packing_cost
                self.price_without_tax = (self.price/(sum([sum([a.amount for a in x.children_tax_ids]) for x in self.product_id.taxes_id])+100))*100
                                         # / ((price/(tax+100)*100)

    @api.onchange('product_id')
    def onchange_product_id(self):
        # force domain on task when project is set
        product_ids = []
        if self._context.get('active_id'):
            commit_id = self.env['commitment.order'].browse(int(self._context.get('active_id')))
            categ_ids = [cat.category_ids.id for cat in commit_id.order_line_ids if cat.remaining_qty>0]
            product_ids = self.env['product.product'].search([('categ_id', 'in', categ_ids),
                                                              ('commitment_ok', '=', False),]).ids
        return {'domain': {
            'product_id': [('id', 'in', product_ids)]
        }}