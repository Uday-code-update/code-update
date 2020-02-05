from odoo import models
import base64
import io
import logging
import requests
import werkzeug.utils
from datetime import datetime
from PIL import Image
from odoo import http, tools, _
from odoo.http import request
from werkzeug.urls import url_encode


class CommitmentOrder(models.AbstractModel):
    _name = 'report.custom_reporting.commitment_order_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, obj):
        worksheet = workbook.add_worksheet('Commitment  Report')
        worksheet.set_column('A:A', 14)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 14)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 14)
        worksheet.set_column('H:H', 14)
        worksheet.set_column('I:I', 14)

        col = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1, })
        # col_right = workbook.add_format({'align': 'right', 'bold': 1, })
        # col.set_font_size(20)
        #
        worksheet.merge_range('A%s:H%s' % (1,1), 'Commitment Report', col)

        worksheet.write('B3', self.env.user.company_id.name, col)

        worksheet.write('C5', self.env.user.company_id.name, col)
        worksheet.write('D5', 'To', col)
        worksheet.write('E5', self.env.user.company_id.name, col)

        worksheet.write('A11', 'Commitment Oder No.', col)
        worksheet.write('B11', 'Price List', col)
        worksheet.write('C11', 'Customer name', col)
        worksheet.write('D11', 'Commitment Date', col)
        worksheet.write('E11', 'Running Date', col)
        worksheet.write('F11', 'Oder Qty', col)
        worksheet.write('G11', 'Booked QTY', col)
        worksheet.write('H11', 'Remaining QTY', col)
        worksheet.write('I11', 'Sales Order QTY', col)
        worksheet.write('J11', 'Status', col)

        i = 12
        commit_ids = self.env['commitment.order']
        domain = []
        # calculate commit ids
        if obj.category_ids:
            domain.append(('order_line_ids.category_ids', 'in', obj.category_ids.ids))
            # commit_ids = commit_ids.search([('order_line_ids.category_ids', 'in', obj.category_ids.ids)]).filtered(lambda self:self.create_date.date() >= obj.from_date and self.create_date.date() <= obj.to_date)
        if obj.partner_ids:
            domain.append(('partner_id', 'in', obj.partner_ids.ids))
        commit_ids = commit_ids.search(domain).filtered(lambda self:self.create_date >= obj.from_date and self.create_date <= obj.to_date)

        col = workbook.add_format({'align': 'center'})
        for com in commit_ids:
            worksheet.write('A%s'%i, com.name, col)
            worksheet.write('B%s'%i, com.price_list_id.name or '', col)
            worksheet.write('C%s'%i, com.partner_id.name or '', col)
            worksheet.write('D%s'%i, str(com.create_date), col)
            worksheet.write('E%s'%i, 'Running date', col)
            worksheet.write('F%s'%i, com.ordered_qty, col)
            worksheet.write('G%s'%i, com.booked_qty, col)
            worksheet.write('H%s'%i, com.remaining_qty, col)
            worksheet.write('I%s'%i, sum([ln.ordered_qty for ln in com.sale_line_ids]), col)
            worksheet.write('J%s'%i, com.state, col)

            i += 1
            worksheet.merge_range('E%s:G%s' % (i, i), 'Category Details', col)
            i += 1
            worksheet.write('E%s' % i, 'Ordered Category', col)
            worksheet.write('F%s' % i, 'Qty', col)
            worksheet.write('G%s' % i, 'Box Price', col)
            i += 1
            for sub_line in com.order_line_ids:
                print("Orderderd Quantity in first sheet in details one ", sub_line.ordered_qty)
                ordered_qty = sub_line.ordered_qty
                print("Orderderd Quantity in first sheet in details one ordered_quantity================", ordered_qty)
                worksheet.write('E%s' % i, sub_line.category_ids.name, col)
                worksheet.write('F%s' % i, ordered_qty, col)
                worksheet.write('G%s' % i, sum([x.box_price for x in com.price_list_id.link_categeries_lines_ids if x.commitment_category.id == sub_line.category_ids.id]), col)

                i += 1

            i += 1

        # next sheet
        worksheet = workbook.add_worksheet('Converted Sale')
        worksheet.set_column('A:A', 14)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 14)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 14)
        worksheet.set_column('H:H', 14)
        worksheet.set_column('J:J', 14)
        worksheet.set_column('K:K', 14)
        worksheet.set_column('L:L', 14)
        worksheet.set_column('M:M', 14)

        col = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1, })
        # col_right = workbook.add_format({'align': 'right', 'bold': 1, })
        # col.set_font_size(20)
        #
        worksheet.merge_range('A%s:M%s' % (1, 1), 'Converted Report', col)

        # worksheet.write('B3', self.env.user.company_id.name, col)
        #
        # worksheet.write('C5', self.env.user.company_id.name, col)
        # worksheet.write('D5', 'To', col)
        # worksheet.write('E5', self.env.user.company_id.name, col)

        worksheet.write('A8', 'Commitment Oder No.', col)
        worksheet.write('B8', 'Sale Order', col)
        worksheet.write('C8', 'Invoice Number', col)
        worksheet.write('D8', 'Customer name ', col)
        worksheet.write('E8', 'Booked QTY', col)
        worksheet.write('F8', 'Adjested QTY', col)
        worksheet.write('G8', 'Adjusted Com No', col)
        worksheet.write('H8', 'Delivey QTY', col)
        worksheet.write('I8', 'Remaining QTY', col)
        worksheet.write('J8', 'Invoiced  QTY', col)
        worksheet.write('K8', 'Status', col)
        worksheet.write('L8', 'Invoice Value', col)
        worksheet.write('M8', 'Paid', col)
        worksheet.write('N8', 'Due', col)

        i = 9

        col = workbook.add_format({'align': 'center'})
        for com in commit_ids:
            for line in com.sale_line_ids:
                worksheet.write('A%s'%i, line.commit_id.name or '', col)
                worksheet.write('B%s'%i, line.sale_id.name or '', col)
                worksheet.write('C%s'%i, 'Invoice Number', col)
                worksheet.write('D%s'%i, line.commit_id.partner_id.name or '', col)
                worksheet.write('E%s'%i, line.booked_qty, col)
                worksheet.write('F%s'%i, line.adjusted_qty, col)
                worksheet.write('G%s'%i, line.adjusted_commitment_order_id.name or '', col)
                worksheet.write('H%s'%i, line.delivery_qty, col)
                worksheet.write('I%s'%i, line.remaining_qty, col)
                worksheet.write('J%s'%i, sum([sum(x.qty_invoiced for x in ln.sale_id.order_line) for ln in com.sale_line_ids]), col)  #sum([ln.ordered_qty for ln in com.sale_line_ids])
                worksheet.write('K%s'%i, line.status, col)
                worksheet.write('L%s'%i, 'Invoice Value', col)   #[ln.sale_id for ln in com.sale_line_ids]
                worksheet.write('M%s'%i, sum([sum([x.amount_total for x in ln.sale_id.invoice_ids]) for ln in com.sale_line_ids]), col)
                worksheet.write('N%s'%i, sum([sum([x.residual for x in ln.sale_id.invoice_ids]) for ln in com.sale_line_ids]), col)    #sum([ln.ordered_qty for ln in com.sale_line_ids])
                i += 1
                worksheet.merge_range('H%s:I%s' % (i,i), 'Product Details', col)
                i += 1
                worksheet.write('I%s' % i, 'Product', col)
                worksheet.write('J%s' % i, 'Qty', col)
                worksheet.write('K%s' % i, 'Price', col)
                i += 1
                for sub_line in line.sale_id.order_line:
                    worksheet.write('I%s' % i, sub_line.product_id.name, col)
                    worksheet.write('J%s' % i, sub_line.product_uom_qty, col)
                    worksheet.write('K%s' % i, sub_line.price_subtotal, col)

                    i += 1

                i += 1

        # next sheet
        worksheet = workbook.add_worksheet('Invoice')
        worksheet.set_column('A:A', 14)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 14)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 14)
        worksheet.set_column('H:H', 14)
        worksheet.set_column('J:J', 14)
        worksheet.set_column('K:K', 14)
        worksheet.set_column('L:L', 14)
        worksheet.set_column('M:M', 14)

        col = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1, })
        # col_right = workbook.add_format({'align': 'right', 'bold': 1, })
        # col.set_font_size(20)
        #
        worksheet.merge_range('A%s:J%s' % (1, 1), 'Invoice Report', col)

        # worksheet.write('B3', self.env.user.company_id.name, col)
        #
        # worksheet.write('C5', self.env.user.company_id.name, col)
        # worksheet.write('D5', 'To', col)
        # worksheet.write('E5', self.env.user.company_id.name, col)

        worksheet.write('A7', 'Commitment Oder No.', col)
        worksheet.write('B7', 'Sale Order', col)
        worksheet.write('C7', 'Invoice Number', col)
        worksheet.write('D7', 'Customer name ', col)
        worksheet.write('E7', 'Commitment Date', col)
        worksheet.write('F7', 'Sales Order Date', col)
        worksheet.write('G7', 'Invoice Date', col)
        worksheet.write('H7', 'Total Value', col)
        worksheet.write('I7', 'Total Value', col)
        worksheet.write('J7', 'Tax Value', col)
        worksheet.write('K7', 'Due Value', col)

        i = 8

        col = workbook.add_format({'align': 'center'})
        for com in commit_ids:
            for line in com.sale_line_ids:
                for inv in line.sale_id.invoice_ids:
                    # total_value = sum([sum([x.amount_total for x in ln.sale_id.invoice_ids]) for ln in com.sale_line_ids])
                    # untaxed_value = sum([sum([x.amount_untaxed for x in ln.sale_id.invoice_ids]) for ln in com.sale_line_ids])
                    worksheet.write('A%s' % i, line.commit_id.name or '', col)
                    worksheet.write('B%s' % i, line.sale_id.name or '', col)
                    worksheet.write('C%s' % i, inv.name, col)
                    worksheet.write('D%s' % i, line.commit_id.partner_id.name or '', col)
                    worksheet.write('E%s' % i, str(line.commit_id.create_date), col)
                    worksheet.write('F%s' % i, str(line.sale_id.create_date), col)
                    worksheet.write('G%s' % i, str(inv.date_invoice), col)    #sum([ln.ordered_qty for ln in com.sale_line_ids])
                    worksheet.write('H%s' % i, inv.amount_total, col)
                    worksheet.write('I%s' % i, inv.amount_total - inv.amount_untaxed, col)
                    # worksheet.write('J%s' % i, sum([sum([x.residual for x in ln.sale_id.invoice_ids]) for ln in com.sale_line_ids]), col)
                    worksheet.write('J%s' % i, inv.residual, col)

                    i += 1
                    worksheet.merge_range('E%s:G%s' % (i, i), 'Product Details', col)
                    i += 1
                    worksheet.write('E%s' % i, 'Product', col)
                    worksheet.write('F%s' % i, 'Qty', col)
                    worksheet.write('G%s' % i, 'Price', col)
                    i += 1
                    for sub_line in inv.invoice_line_ids:
                        worksheet.write('E%s' % i, sub_line.product_id.name, col)
                        worksheet.write('F%s' % i, sub_line.quantity, col)
                        worksheet.write('G%s' % i, sub_line.product_id.list_price, col)

                        i += 1

                    i += 1


class PPVReport(models.AbstractModel):
    _name = 'report.custom_reporting.ppvcommitment_order_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, obj):
        worksheet = workbook.add_worksheet('Gate Pass')
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 14)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 14)
        worksheet.set_column('H:H', 14)
        worksheet.set_column('I:I', 14)

        col = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1, })
        # col_right = workbook.add_format({'align': 'right', 'bold': 1, })
        # col.set_font_size(20)
        #
        worksheet.merge_range('A%s:E%s' % (1, 1), self.env.user.company_id.name, col)

        worksheet.write('A2', 'Delivery Report Date', col)
        worksheet.write('B2', str(datetime.now().date()), col)

        worksheet.write('A3', 'Vehicle Number', col)
        worksheet.write('B3', obj.vechile_no.license_plate or '', col)

        worksheet.write('A4', 'Vehicle Production Planned Number', col)
        worksheet.write('B4', obj.name or '', col)

        worksheet.write('A4', 'Driver Name', col)
        worksheet.write('B4', obj.vechile_no.driver_id.name or '', col)

        worksheet.merge_range('A6:D6', 'Gate Pass', col)

        pp_uom_ids = set([x.product_name_id.uom_id for x in obj.product_detail_ids])
        worksheet.write('A7', 'Sr. No.', col)
        worksheet.write('B7', 'Category', col)
        cj = 2
        for j in pp_uom_ids:
            worksheet.write(6, cj, j.name, col)
            cj += 1
        worksheet.write(6, cj, 'Total', col)

        col = workbook.add_format({'align': 'center', 'valign': 'vcenter', })

        obj.Product_Details()
        pp_categ_ids = set([x.product_name_id.categ_id for x in obj.product_detail_ids])

        gate_pass_data = []

        if obj.sale_order_line_ids:
            # self.product_detail_ids = []
            for line in obj.product_detail_ids:
                line.unlink()
            for sale in obj.sale_order_line_ids:
                for line in sale.sale_id.order_line:
                    obj.product_detail_ids = [(0, 0, {
                        "product_name_id": line.product_id.id,
                        "qty": line.product_uom_qty,
                        "delivery_qty": line.qty_delivered,
                        "delivery_id": sale.sale_id.picking_ids and sale.sale_id.picking_ids[0].id
                    })]

        for cat in pp_categ_ids:
            categ_id = ""
            categ_id_seq = ""
            uom_id_temp = []

            for uom in pp_uom_ids:
                qty = 0
                for x in obj.product_detail_ids:
                    if uom.id == x.product_name_id.uom_id.id:
                        if x.product_name_id.categ_id.id == cat.id:
                            categ_id_seq = cat.commit_seq
                            categ_id = cat.name
                            uom_id = uom.name
                            qty += x.qty
                uom_id_temp.append((uom_id, qty))
            gate_pass_data.append({
                "categ_id_seq": categ_id_seq,
                "categ_id": categ_id,
                "uom_ids": uom_id_temp
                # "uom_id": uom_id,
                # "qty": qty,
            })

        i = 8
        for gt in gate_pass_data:
            worksheet.write('A%s' % str(i), gt.get('categ_id_seq'), col)
            worksheet.write('B%s' % str(i), gt.get('categ_id'), col)
            cj = 2
            temp_total_um = 0
            for j in gt.get('uom_ids'):
                worksheet.write(i-1, cj, j[1], col)
                cj += 1
                temp_total_um+=j[1]
            worksheet.write(i - 1, cj, temp_total_um, col)
            i+=1

        worksheet.write('B%s' % str(i), 'Total', col)
        cj = 2
        for x in pp_uom_ids:
            qty = sum([y.qty for y in obj.product_detail_ids if y.product_name_id.uom_id.id == x.id])
            worksheet.write(i - 1, cj, qty, col)
            cj += 1
        i += 1


        # for x in obj.product_detail_ids:
        #     worksheet.write('A%s'%str(i), x.product_name_id.categ_id.commit_seq, col)
        #     worksheet.write('B%s'%str(i), x.product_name_id.categ_id.name, col)
        #     worksheet.write('C%s'%str(i), x.product_name_id.uom_id.name, col)
        #     i+=1





        worksheet = workbook.add_worksheet('Delivery  Report')
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 14)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 14)
        worksheet.set_column('H:H', 14)
        worksheet.set_column('I:I', 14)

        col = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': 1, })
        # col_right = workbook.add_format({'align': 'right', 'bold': 1, })
        # col.set_font_size(20)
        #

        worksheet.write('A1', 'Detail Delivery Report', col)
        col = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        i=3
        for line in obj.sale_order_line_ids:
            worksheet.write('A%s'%str(i), 'Customer Name', col)
            worksheet.write('B%s'%str(i), line.sale_id.partner_id.name, col)

            co_no = ""
            for ln in line.sale_id.order_line:
                co_no += (ln.commit_id.name or '') +" , "

            worksheet.write('D%s' % str(i), 'Commitment Order No', col)
            worksheet.write('E%s' % str(i), co_no, col)

            i+=1
            worksheet.write('A%s' % str(i+1), 'City', col)
            worksheet.write('B%s' % str(i+1), line.sale_id.partner_id.city or '', col)

            worksheet.write('D%s' % str(i), 'Sale Order No', col)
            worksheet.write('E%s' % str(i), line.sale_id.name, col)

            i+=1
            pi_no = ""
            for ln in line.sale_id.picking_ids:
                pi_no += ln.name +" , "
            worksheet.write('D%s' % str(i), 'Delivery Order No', col)
            worksheet.write('E%s' % str(i), pi_no, col)

            i+=2
            worksheet.merge_range('A%s:D%s' % (str(i), str(i)), 'Product Detail Report', col)
            i+=1
            worksheet.write('A%s' % str(i), 'Sr. No', col)
            worksheet.write('B%s' % str(i), 'Product', col)
            worksheet.write('C%s' % str(i), 'Qty', col)

            i+=1
            total_qty = 0
            delivery_detail = []
            for sn in line.sale_id.order_line:
                delivery_detail.append({
                    "name": obj.name,
                    "product_name": sn.product_id.name,
                    "qty": sn.product_uom_qty,
                })
            set_delivery_detail = []
            if delivery_detail:
                set_delivery_detail = list({v['product_name']:v for v in delivery_detail}.values())

            # from collections import defaultdict
            # temp = defaultdict(list)
            # for elem in delivery_detail:
            #     temp[elem['product_name']].extend(elem['qty'])
            # Output = [{"product_name": y, "qty": x} for x, y in temp.items()]

            for stdl in set_delivery_detail:
                temp_qty = 0
                for ln in delivery_detail:
                    if stdl['product_name'] == ln['product_name']:
                        temp_qty+=ln['qty']
                        total_qty+=ln['qty']

                worksheet.write('A%s' % str(i), stdl['name'], col)
                worksheet.write('B%s' % str(i), stdl['product_name'], col)
                worksheet.write('C%s' % str(i), temp_qty, col)
                i += 1
            worksheet.write('B%s'%str(i), 'Total', col)
            worksheet.write('C%s' % str(i), total_qty, col)
            i+=2