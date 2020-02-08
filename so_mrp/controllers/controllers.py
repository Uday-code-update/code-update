# -*- coding: utf-8 -*-
from odoo import http

# class Mrp(http.Controller):
#     @http.route('/mrp/mrp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp/mrp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp.listing', {
#             'root': '/mrp/mrp',
#             'objects': http.request.env['mrp.mrp'].search([]),
#         })

#     @http.route('/mrp/mrp/objects/<model("mrp.mrp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp.object', {
#             'object': obj
#         })