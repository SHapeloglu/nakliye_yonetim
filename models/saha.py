from odoo import models, fields

class Saha(models.Model):
    _name = 'nakliye.saha'
    _description = 'Saha'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Saha Adı', required=True, tracking=True)

    # Her saha bir şantiyeye bağlı
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True,
        tracking=True
    )

    # Sahanın fiziksel konumu — saha ilerledikçe güncellenir
    # Döküm/ocak km hesabı buradan + cari koordinatından otomatik hesaplanacak
    partner_latitude = fields.Float(string='Enlem', tracking=True)
    partner_longitude = fields.Float(string='Boylam', tracking=True)

    # TODO Faz 3: domain gruplar tanımlandıktan sonra
    # group_nakliye_formen ile kısıtlanacak
    formen_ids = fields.Many2many(
        'res.users',
        string='Formenler'
    )

    aktif = fields.Boolean(string='Aktif', default=True, tracking=True)