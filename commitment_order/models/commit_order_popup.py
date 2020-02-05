# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError, UserError

class SaleOrderPopup1(models.TransientModel):
    _name = "sale.order.transient.new"

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_agent_type','=','customer')])
    line_ids = fields.One2many('sale.order.transient.line.new', 'sale_id')
    # action_commitment = fields.Selection([('auto_create_commitment', 'Auto Create Commitment Order'),
    #                                            ('merge_commitment_order', 'Merge Order Commitment')])

    def create_sale_order(self):
        if self.partner_id:
            commit_id = self.env['commitment.order'].search([('partner_id', '=', self.partner_id.id)])

            if not commit_id:
                price_list_id = self.env['product.pricelist'].search([], order='commitment_date desc')
                if price_list_id:
                    price_list_id = price_list_id.filtered(
                        lambda self: str(self.commitment_date) == str(datetime.now().date()))
                    if price_list_id:
                        price_list_id = price_list_id[0]

                categ_detail_ids = []

                pp_categ_ids = set([x.product_id.categ_id for x in self.line_ids])
                order_line = []
                total_qty = 0
                for cat in pp_categ_ids:
                    temp_qty = 0
                    for line in self.line_ids:

                        # Calculate price
                        price_list_idcl = price_list_id.link_categeries_lines_ids
                        commit_price = sum(
                            [x.commit_price for x in price_list_idcl if
                             x.commitment_category.id == line.product_id.categ_id.id])

                        price = (line.product_id.weight * commit_price) + line.product_id.packing_cost
                        price_without_tax = (price / (sum(
                            [sum([a.amount for a in x.children_tax_ids]) for x in
                             line.product_id.taxes_id]) + 100)) * 100
                        # end
                        order_line.append((0, 0, dict(
                            customer_lead=1,
                            name=line.product_id.name,
                            product_id=line.product_id.id,
                            price_unit=price_without_tax,
                            product_uom_qty=line.qty,
                        )))

                        if line.product_id.categ_id.id == cat.id:
                            temp_qty += line.qty
                            total_qty += line.qty
                    categ_detail_ids.append((0, 0, {
                        "category_ids": cat.id,
                        "ordered_qty": temp_qty,
                        "delivery_qty": temp_qty,
                        "sales_order_qty": temp_qty,
                        "remaining_qty": 0
                    }))
                # commit_id.order_line_ids = categ_detail_ids


                commit_id = self.env['commitment.order'].create({
                    "partner_id": self.partner_id.id,
                    "user_id": self.partner_id.user_id.id,
                    "price_list_id": price_list_id.id,
                    "expiry_date": str(datetime.now().date()+timedelta(days=7)),
                    "order_line_ids": categ_detail_ids
                })

                for ol in order_line:
                    ol[2]['commit_id'] = commit_id.id

                for line in commit_id.order_line_ids:
                    get_line = [x for x in categ_detail_ids if x[2]['category_ids'] == line.category_ids.id]
                    line.write({
                        "delivery_qty": get_line[0][2]['delivery_qty'],
                        "sales_order_qty": get_line[0][2]['sales_order_qty'],
                        "remaining_qty": 0
                    })


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

                sale_id.order_line = order_line
                commit_id.sale_line_ids = [(0, 0, {
                    'name': sale_id.name,
                    'sale_id': sale_id.id,
                    'ordered_qty': total_qty,
                    # 'adjusted_qty': new_commit_id_total_qty,
                    # 'adjusted_commitment_order_id': [(4, new_commit_id.id)],
                    # 'booked_qty': commit_id,
                    # 'remaining_qty': commit_id,
                    # 'delivery_qty': commit_id,
                })]



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

            else:

                sale_order_book_com_ids = []

                chklncommit_ids = commit_id

                pp_categ_ids = set([x.product_id.categ_id for x in self.line_ids])

                category_details = []
                for cat in pp_categ_ids:
                    temp_qty = 0
                    product_dict = []
                    for line in self.line_ids:
                        if cat.id == line.product_id.categ_id.id:
                            temp_qty += line.qty
                            product_dict.append({
                                "product_id": line.product_id,
                                "qty": line.qty
                            })
                    category_details.append({
                        "categ_id": cat.id,
                        "qty": temp_qty,
                        "product_dict": product_dict
                    })
                order_line = []

                for com in chklncommit_ids:
                    for line in com.order_line_ids:
                        if line.remaining_qty > 0:
                            temp_line = [x for x in category_details if x['categ_id'] == line.category_ids.id]


                            if line.category_ids.id == temp_line[0]['categ_id']:

                                # create order line
                                for pro in temp_line[0]['product_dict']:
                                    sale_order_book_com_ids.append(com)
                                    price_list_id1 = com.price_list_id.link_categeries_lines_ids
                                    commit_price1 = sum(
                                        [x.commit_price for x in price_list_id1 if
                                         x.commitment_category.id == pro['product_id'].categ_id.id])

                                    price = (pro['product_id'].weight * commit_price1) + pro['product_id'].packing_cost
                                    price_without_tax = (price / (sum(
                                        [sum([a.amount for a in x.children_tax_ids]) for x in
                                         pro['product_id'].taxes_id]) + 100)) * 100

                                    if pro['qty'] > line.remaining_qty:
                                        order_line.append((0, 0, {
                                            "customer_lead":1,
                                            "name":pro['product_id'].name,
                                            "product_id":pro['product_id'].id,
                                            "price_unit":price_without_tax,
                                            "commit_id": com.id,
                                            "product_uom_qty": line.remaining_qty
                                        }))
                                        pro['qty'] -= line.remaining_qty

                                        line.delivery_qty = line.remaining_qty
                                        line.sales_order_qty = line.remaining_qty
                                        line.remaining_qty = 0

                                    elif line.remaining_qty > pro['qty']:
                                        order_line.append((0, 0, {
                                            "customer_lead": 1,
                                            "name": pro['product_id'].name,
                                            "product_id": pro['product_id'].id,
                                            "price_unit": price_without_tax,
                                            "commit_id": com.id,
                                            "product_uom_qty": pro['qty']
                                        }))


                                        remaining_qty = pro['qty']
                                        pro['qty'] = 0

                                        line.remaining_qty -= remaining_qty
                                        line.delivery_qty += remaining_qty
                                        line.sales_order_qty += remaining_qty

                                    else:
                                        order_line.append((0, 0, {
                                            "customer_lead": 1,
                                            "name": pro['product_id'].name,
                                            "product_id": pro['product_id'].id,
                                            "price_unit": price_without_tax,
                                            "commit_id": com.id,
                                            "product_uom_qty": pro['qty']
                                        }))
                                        pro['qty'] = 0

                                        line.delivery_qty += line.remaining_qty
                                        line.sales_order_qty += line.remaining_qty
                                        line.remaining_qty = 0
                                        break







                                # end



                    pass

                for cat in category_details:
                    cat['qty'] = sum(x['qty'] for x in cat['product_dict'])

                new_commit_lines = []
                # calculating pricelist
                newprice_list_id_at = self.env['product.pricelist'].search([], order='commitment_date desc')
                if newprice_list_id_at:
                    newprice_list_id_at = newprice_list_id_at.filtered(
                        lambda self: str(self.commitment_date) == str(datetime.now().date()))
                    if newprice_list_id_at:
                        newprice_list_id_at = newprice_list_id_at[0]
                # end
                for cat in category_details:
                    if cat['qty'] != 0:
                        new_commit_lines.append((0, 0, {
                            "category_ids": cat['categ_id'],
                            "ordered_qty": cat['qty'],
                            "delivery_qty": cat['qty'],
                            "sales_order_qty": cat['qty'],
                            "remaining_qty": 0
                        }))


                # create co

                new_commit_id = self.env['commitment.order'].create({
                    'partner_id': self.partner_id.id,
                    'user_id': self.partner_id.user_id.id,
                    'price_list_id': newprice_list_id_at.id,
                    'expiry_date': str(datetime.now().date()+timedelta(days=7)),
                    'order_line_ids': new_commit_lines
                })
                new_commit_id.state = "completed"


                # create new order line
                for cat in category_details:
                    if cat['qty'] != 0:
                        for pro in cat['product_dict']:
                            if pro['qty'] != 0:
                                price_list_id1 = new_commit_id.price_list_id.link_categeries_lines_ids
                                commit_price1 = sum(
                                    [x.commit_price for x in price_list_id1 if
                                     x.commitment_category.id == pro['product_id'].categ_id.id])

                                price = (pro['product_id'].weight * commit_price1) + pro['product_id'].packing_cost
                                price_without_tax = (price / (sum(
                                    [sum([a.amount for a in x.children_tax_ids]) for x in
                                     pro['product_id'].taxes_id]) + 100)) * 100
                                order_line.append((0, 0, {
                                    "customer_lead": 1,
                                    "name": pro['product_id'].name,
                                    "product_id": pro['product_id'].id,
                                    "price_unit": price_without_tax,
                                    "commit_id": new_commit_id.id,
                                    "product_uom_qty": pro['qty']
                                }))
                # end
                sale_order_book_com_ids.append(new_commit_id)

                sale_id = self.env['sale.order'].create(dict(
                    partner_id=new_commit_id.partner_id.id,
                    partner_invoice_id=new_commit_id.partner_id.id,
                    partner_shipping_id=new_commit_id.partner_id.id,
                    company_id=self.env.user.company_id.id,
                    currency_id=self.env.user.company_id.currency_id.id,
                    date_order=datetime.now(),
                    # name='fg',
                    order_line=order_line,
                    picking_policy='direct',
                    pricelist_id=new_commit_id.price_list_id.id,
                    warehouse_id=self.env['stock.warehouse'].search([], limit=1).id
                ))

                newsale_order_book_com_ids = set(list(sale_order_book_com_ids))
                for com in newsale_order_book_com_ids:
                    com.sale_line_ids = [(0, 0, {
                        'name': sale_id.name,
                        'sale_id': sale_id.id,
                        'ordered_qty': sum(x.qty for x in self.line_ids),
                        # 'adjusted_qty': mrln[2]['product_uom_qty'],
                        # 'adjusted_commitment_order_id': [(4, new_commit_id.id)],
                        # 'booked_qty': commit_id,
                        # 'remaining_qty': commit_id,
                        # 'delivery_qty': commit_id,
                    })]

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




class SaleOrderLineTransient1(models.TransientModel):
    _name = "sale.order.transient.line.new"

    sale_id = fields.Many2one('sale.order.transient.new')
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

    # @api.onchange('product_id')
    # def compute_category_id(self):
    #     if self.product_id:
    #         self.category_id = self.product_id.categ_id.id
    #
    #         if self._context.get('active_id'):
    #             commit_id = self.env['commitment.order'].browse(int(self._context.get('active_id')))
    #             price_list_id = commit_id.price_list_id.link_categeries_lines_ids
    #             commit_price = sum([x.commit_price for x in price_list_id if x.commitment_category.id == self.product_id.categ_id.id])
    #
    #             self.price = (self.product_id.weight * commit_price) + self.product_id.packing_cost
    #             self.price_without_tax = (self.price/(sum([sum([a.amount for a in x.children_tax_ids]) for x in self.product_id.taxes_id])+100))*100
                                         # / ((price/(tax+100)*100)

    @api.onchange('product_id')
    def onchange_product_id(self):
        # force domain on task when project is set
        product_ids = []
        # if self._context.get('active_id'):
        #     commit_id = self.env['commitment.order'].browse(int(self._context.get('active_id')))
        #     categ_ids = [cat.category_ids.id for cat in commit_id.order_line_ids if cat.remaining_qty>0]
        product_ids = self.env['product.product'].search([('commitment_ok', '=', False),]).ids
        return {'domain': {
            'product_id': [('id', 'in', product_ids)]
        }}