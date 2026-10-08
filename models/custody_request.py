# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CustodyRequest(models.Model):
    _name = 'custody.request'
    _description = 'Zimmet Talebi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(
        string='Talep No', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('Yeni')
    )
    employee_id = fields.Many2one(
        'hr.employee', 
        string='Talep Eden Mühendis', 
        required=True, 
        default=lambda self: self.env.user.employee_id,
        tracking=True
    )
    equipment_id = fields.Many2one(
        'custody.equipment', 
        string='Talep Edilen Ekipman', 
        required=True, 
        tracking=True
    )
    start_date = fields.Date(
        string='Başlangıç Tarihi', 
        required=True, 
        default=fields.Date.context_today, 
        tracking=True
    )
    end_date = fields.Date(
        string='Planlanan İade Tarihi', 
        required=True, 
        tracking=True
    )
    return_date = fields.Date(
        string='Fiili İade Tarihi', 
        readonly=True, 
        copy=False, 
        tracking=True
    )
    
    purpose = fields.Text(string='Kullanım Amacı / Gerekçe')
    
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('to_approve', 'Onay Bekliyor'),
        ('approved', 'Onaylandı'),
        ('delivered', 'Teslim Edildi'),
        ('returned', 'İade Alındı'),
        ('rejected', 'Reddedildi'),
    ], string='Durum', default='draft', tracking=True)

    is_overdue = fields.Boolean(
        string='İade Tarihi Geçti mi?', 
        compute='_compute_is_overdue', 
        search='_search_is_overdue'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Yeni')) == _('Yeni'):
                vals['name'] = self.env['ir.sequence'].next_by_code('custody.request') or _('Yeni')
        return super().create(vals_list)

    @api.depends('end_date', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for req in self:
            req.is_overdue = bool(req.state == 'delivered' and req.end_date and req.end_date < today)

    def _search_is_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        if operator == '=' and value is True:
            return [('state', '=', 'delivered'), ('end_date', '<', today)]
        return [('state', '=', 'delivered'), ('end_date', '>=', today)]

    # --- 1. Katman: Form Doldurulurken Canlı Uyarı (@api.onchange) ---
    @api.onchange('equipment_id', 'start_date', 'end_date')
    def _onchange_check_availability(self):
        if self.equipment_id and self.start_date and self.end_date:
            if self.end_date < self.start_date:
                return {
                    'warning': {
                        'title': _('Geçersiz Tarih Aralığı'),
                        'message': _('Planlanan iade tarihi, başlangıç tarihinden önce olamaz!'),
                    }
                }
            
            conflicts = self.search([
                ('id', '!=', self._origin.id),
                ('equipment_id', '=', self.equipment_id.id),
                ('state', 'in', ['approved', 'delivered']),
                ('start_date', '<=', self.end_date),
                ('end_date', '>=', self.start_date),
            ])
            if conflicts:
                conflict_details = ", ".join(
                    [f"{c.name} ({c.start_date} - {c.end_date})" for c in conflicts]
                )
                return {
                    'warning': {
                        'title': _('Dikkat: Ekipman Bu Tarihlerde Dolu!'),
                        'message': _(
                            'Seçtiğiniz ekipman belirtilen tarih aralığında başka bir talep için ayrılmıştır.\n\n'
                            'Çakışan Talep: %s\n\n'
                            'Farklı bir tarih aralığı seçebilir veya Takvim görünümünden uygun boşlukları inceleyebilirsiniz.'
                        ) % conflict_details,
                    }
                }

    # --- 2. Katman: Kesin Veritabanı Doğrulaması (@api.constrains) ---
    @api.constrains('start_date', 'end_date', 'equipment_id', 'state')
    def _check_date_conflict(self):
        for req in self:
            if req.state in ['draft', 'rejected', 'returned']:
                continue
            if req.end_date < req.start_date:
                raise ValidationError(_("Planlanan iade tarihi başlangıç tarihinden önce olamaz!"))
            
            conflicts = self.search([
                ('id', '!=', req.id),
                ('equipment_id', '=', req.equipment_id.id),
                ('state', 'in', ['approved', 'delivered']),
                ('start_date', '<=', req.end_date),
                ('end_date', '>=', req.start_date),
            ])
            if conflicts:
                conflict_names = ", ".join(conflicts.mapped('name'))
                raise ValidationError(_(
                    "Bu ekipman seçilen tarih aralığında (%s - %s) zaten tahsis edilmiş durumda! Çakışan Talep: %s"
                ) % (req.start_date, req.end_date, conflict_names))

    # --- Durum Butonları İş Akışı ---
    def action_submit(self):
        self.write({'state': 'to_approve'})

    def action_approve(self):
        self._check_date_conflict()
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_deliver(self):
        self._check_date_conflict()
        self.write({'state': 'delivered'})

    def action_return(self):
        self.ensure_one()
        return {
            'name': _('Ekipman İade Kabul ve Kondisyon Kontrolü'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }