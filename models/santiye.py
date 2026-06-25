from odoo import models, fields

class Santiye(models.Model):
    _name = 'nakliye.santiye'
    _description = 'Şantiye'
    # mail.thread → chatter ve tracking desteği
    # mail.activity.mixin → aktivite hatırlatma desteği
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Şantiye adı — toplanma yeri, idari birim
    name = fields.Char(string='Şantiye Adı', required=True, tracking=True)
    # Kod — raporlarda kısa referans olarak kullanılır
    kod = fields.Char(string='Kod', required=True, tracking=True)
    # TODO Faz 3: domain — group_nakliye_santiye_muhasebe ile kısıtlanacak
    # Sadece muhasebe müdürü atama yapabilir
    muhasebeci_ids = fields.Many2many(
        'res.users',
        string='Muhasebeciler'
    )
    # Pasife alınca ir.rule devreye girer — şantiye muhasebecisi göremez
    aktif = fields.Boolean(string='Aktif', default=True, tracking=True)