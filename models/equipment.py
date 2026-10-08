# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api

class CustodyEquipment(models.Model):
    _name = 'custody.equipment'
    _description = 'Ekipman Tanımı'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ekipman Adı', required=True, tracking=True)
    serial_number = fields.Char(string='Seri Numarası', required=True, copy=False, tracking=True)
    category = fields.Selection([
        ('oscilloscope', 'Osiloskop'),
        ('laptop', 'Laptop / PC'),
        ('measurement', 'Ölçüm Cihazı'),
        ('other', 'Diğer'),
    ], string='Kategori', required=True, default='other', tracking=True)
    
    status = fields.Selection([
        ('available', 'Müsait'),
        ('reserved', 'Rezerve (Onaylandı)'),
        ('assigned', 'Zimmette (Teslim Edildi)'),
        ('maintenance', 'Bakımda / Arızalı'),
    ], string='Durum', default='available', tracking=True, compute='_compute_status', store=True)

    current_assignee_id = fields.Many2one(
        'hr.employee', 
        string='Mevcut Zimmetli', 
        compute='_compute_status', 
        store=True,
        tracking=True
    )
    
    request_ids = fields.One2many(
        'custody.request', 
        'equipment_id', 
        string='Zimmet Geçmişi ve Talepler'
    )
    
    request_count = fields.Integer(string='Talep Sayısı', compute='_compute_request_count')
    note = fields.Text(string='Açıklama / Notlar')

    @api.depends('request_ids')
    def _compute_request_count(self):
        for equipment in self:
            equipment.request_count = len(equipment.request_ids)

    @api.depends('request_ids.state', 'request_ids.employee_id')
    def _compute_status(self):
        for equipment in self:
            delivered_req = equipment.request_ids.filtered(lambda r: r.state == 'delivered')
            approved_req = equipment.request_ids.filtered(lambda r: r.state == 'approved')
            
            if delivered_req:
                equipment.status = 'assigned'
                equipment.current_assignee_id = delivered_req[0].employee_id
            elif approved_req:
                equipment.status = 'reserved'
                equipment.current_assignee_id = approved_req[0].employee_id
            else:
                if equipment.status != 'maintenance':
                    equipment.status = 'available'
                equipment.current_assignee_id = False

    def action_view_requests(self):
        self.ensure_one()
        return {
            'name': f"{self.name} - Zimmet Talepleri",
            'type': 'ir.actions.act_window',
            'res_model': 'custody.request',
            'view_mode': 'list,form,calendar',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
    def action_set_available(self):
        self.ensure_one()
        self.status = 'available'
        body_html = Markup("<b>Bilgi:</b> Cihazın arıza/bakım süreci tamamlandı ve yeniden <b>Müsait</b> durumuna alındı.")
        self.message_post(body=body_html)