# -*- coding: utf-8 -*-
# from odoo import http


# class EquipmentCustody(http.Controller):
#     @http.route('/equipment_custody/equipment_custody', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/equipment_custody/equipment_custody/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('equipment_custody.listing', {
#             'root': '/equipment_custody/equipment_custody',
#             'objects': http.request.env['equipment_custody.equipment_custody'].search([]),
#         })

#     @http.route('/equipment_custody/equipment_custody/objects/<model("equipment_custody.equipment_custody"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('equipment_custody.object', {
#             'object': obj
#         })

