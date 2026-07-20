from odoo import models, fields, api

class MaintenanceEquipment(models.Model):
    # hr.equipment modelini extend ediyoruz
    # Odoo'nun standart ekipman modeline zimmet alanları ekliyoruz
    _inherit = 'maintenance.equipment'

    # Şantiye — her ekipman bir şantiyeye ait
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        tracking=True
    )

    # Zimmet alan çalışan
    zimmet_alan_id = fields.Many2one(
        'hr.employee',
        string='Zimmet Alan',
        tracking=True
    )

    # Zimmet tarihi
    zimmet_tarihi = fields.Date(
        string='Zimmet Tarihi',
        tracking=True
    )

    # İade tarihi — dolunca zimmet kapanmış sayılır
    iade_tarihi = fields.Date(
        string='İade Tarihi',
        tracking=True
    )

    # Zimmet durumu — computed field
    # iade_tarihi doluysa iade edilmiş, dolmadıysa zimmetli
    zimmet_durumu = fields.Selection([
        ('zimmetli', 'Zimmetli'),
        ('iade_edildi', 'İade Edildi'),
        ('kayip', 'Kayıp'),
    ], string='Zimmet Durumu', default='zimmetli', tracking=True)

    # Zimmet notu
    zimmet_notu = fields.Text(string='Zimmet Notu')