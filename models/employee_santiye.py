from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeEmployeeSantiye(models.Model):
    _name = 'nakliye.employee.santiye'
    _description = 'Çalışan Şantiye Atama Geçmişi'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Çalışan',
        required=True,
        ondelete='cascade'
    )
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True
    )
    baslangic_tarihi = fields.Date(string='Başlangıç Tarihi', required=True)
    bitis_tarihi = fields.Date(string='Bitiş Tarihi')
    gecis_nedeni = fields.Selection([
        ('ilk_atama', 'İlk Atama'),
        ('santiye_degisikligi', 'Şantiye Değişikliği'),
        ('gecici_gorev', 'Geçici Görev'),
        ('isten_ayrilma', 'İşten Ayrılma'),
    ], string='Geçiş Nedeni', required=True)
    notlar = fields.Text(string='Notlar')
    # Kaydı oluşturan kullanıcı — default olarak giriş yapan kullanıcı gelir
    # lambda self: self.env.user → kayıt oluşturulurken anlık kullanıcıyı alır
    tanimlayan_id = fields.Many2one(
        'res.users',
        string='Tanımlayan',
        default=lambda self: self.env.user
    )
    # Aktif atama — bitis_tarihi dolunca sistem False yapar
    aktif = fields.Boolean(string='Aktif', default=True)

    # Bir çalışanın aynı anda yalnızca bir aktif şantiye ataması olabilir
    @api.constrains('employee_id', 'aktif')
    def _check_unique_aktif_atama(self):
        for kayit in self:
            if kayit.aktif:
                duplicate = self.search([
                    ('employee_id', '=', kayit.employee_id.id),
                    ('aktif', '=', True),
                    ('id', '!=', kayit.id)
                ])
                if duplicate:
                    raise ValidationError(
                        f"{kayit.employee_id.name} için zaten aktif "
                        f"bir şantiye ataması var!"
                    )