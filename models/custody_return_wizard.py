# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api, _

class CustodyReturnWizard(models.TransientModel):
    _name = 'custody.return.wizard'
    _description = 'Zimmet İade ve Durum Kontrolü'

    request_id = fields.Many2one('custody.request', string='Zimmet Talebi', required=True)
    equipment_id = fields.Many2one(
        related='request_id.equipment_id', 
        string='Ekipman', 
        readonly=True
    )
    return_condition = fields.Selection([
        ('intact', 'Eksiksiz ve Sağlam'),
        ('damaged', 'Hasarlı / Arızalı'),
        ('calibration_needed', 'Kalibrasyon Gerekli'),
    ], string='İade Durumu / Kondisyon', default='intact', required=True)
    
    damage_note = fields.Text(string='Arıza / Durum Açıklaması')

    def action_confirm_return(self):
        self.ensure_one()
        req = self.request_id
        
        # Talebi kapat
        req.write({
            'state': 'returned',
            'return_date': fields.Date.context_today(self),
        })
        
        cond_label = dict(self._fields['return_condition'].selection).get(self.return_condition)
        note_text = self.damage_note or 'Belirtilmedi'
        
        # Arıza veya kalibrasyon varsa ekipmanın durumunu güncelle
        if self.return_condition in ['damaged', 'calibration_needed']:
            req.equipment_id.status = 'maintenance'
            equip_msg = Markup(
                "<b>DİKKAT:</b> Ekipman iade edilirken kondisyon sorunu bildirildi!<br/>"
                "<b>Durum:</b> %s<br/>"
                "<b>Açıklama:</b> %s"
            ) % (cond_label, note_text)
            req.equipment_id.message_post(body=equip_msg)
        
        # Talep geçmişine log düş
        req_msg = Markup(
            "Ekipman teslim alındı.<br/>"
            "<b>Kondisyon:</b> %s<br/>"
            "<b>Not:</b> %s"
        ) % (cond_label, self.damage_note or '-')
        req.message_post(body=req_msg)
        
        return {'type': 'ir.actions.act_window_close'}