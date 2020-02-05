# -*- coding: utf-8 -*-
from odoo import http

# class MrpCreation(http.Controller):
#     @http.route('/mrp_creation/mrp_creation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_creation/mrp_creation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_creation.listing', {
#             'root': '/mrp_creation/mrp_creation',
#             'objects': http.request.env['mrp_creation.mrp_creation'].search([]),
#         })

#     @http.route('/mrp_creation/mrp_creation/objects/<model("mrp_creation.mrp_creation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_creation.object', {
#             'object': obj
#         })