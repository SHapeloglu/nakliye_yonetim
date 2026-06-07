from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeYakitFisi(models.Model):
    _name = 'nakliye.yakit.fisi'
    _description = 'Yakıt Fişi'
    # mail.thread → chatter ve tracking desteği
    # mail.activity.mixin → aktivite hatırlatma desteği
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Bağlı plan satırı — hangi araç, hangi gün
    plan_satir_id = fields.Many2one(
        'nakliye.plan.satir',
        string='Plan Satırı',
        required=True,
        tracking=True
    )

    # Plan satırından otomatik gelen bilgiler
    # related + store=True → veritabanına kaydedilir, raporlarda kullanılır
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        related='plan_satir_id.plan_id.santiye_id',
        store=True
    )
    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        related='plan_satir_id.arac_id',
        store=True
    )
    tarih = fields.Date(
        string='Tarih',
        related='plan_satir_id.plan_id.tarih',
        store=True
    )

    # Yakıt bilgileri
    # Akaryakıt istasyonu — tedarikçi olarak res.partner'dan seçilir
    istasyon_id = fields.Many2one(
        'res.partner',
        string='Akaryakıt İstasyonu',
        tracking=True
    )

    # Litre ve birim fiyat — toplam tutar otomatik hesaplanır
    litre = fields.Float(string='Litre', required=True, tracking=True)
    birim_fiyat = fields.Float(
        string='Birim Fiyat (TL/lt)',
        required=True,
        tracking=True
    )

    # Toplam tutar — hesaplanmış alan
    # @api.depends → litre veya birim_fiyat değişince yeniden hesaplanır
    toplam_tutar = fields.Float(
        string='Toplam Tutar (TL)',
        compute='_compute_toplam_tutar',
        store=True
    )

    # Fiş numarası — akaryakıt fişinin orijinal numarası
    fis_no = fields.Char(string='Fiş No', tracking=True)

    # Fiş durumu — iş akışı bu alan üzerinden yönetilir
    # taslak → formen girdi
    # onaylandi → muhasebeci onayladı, hakediş hesabına dahil edilir
    # iptal → yanlış girilmiş, hakediş dışında tutulur
    durum = fields.Selection([
        ('taslak', 'Taslak'),
        ('onaylandi', 'Onaylandı'),
        ('iptal', 'İptal'),
    ], string='Durum', default='taslak', tracking=True)

    notlar = fields.Text(string='Notlar')

    @api.depends('litre', 'birim_fiyat')
    def _compute_toplam_tutar(self):
        for kayit in self:
            # Toplam tutar = litre × birim fiyat
            kayit.toplam_tutar = kayit.litre * kayit.birim_fiyat

    @api.constrains('litre', 'birim_fiyat')
    def _check_degerler(self):
        for kayit in self:
            # Negatif değer olamaz
            if kayit.litre < 0:
                raise ValidationError("Litre değeri negatif olamaz!")
            if kayit.birim_fiyat < 0:
                raise ValidationError("Birim fiyat negatif olamaz!")

    def action_onayla(self):
        # Taslak → Onaylandı geçişi
        # Litre girilmemişse onaylanamaz
        for kayit in self:
            if kayit.litre <= 0:
                raise ValidationError(
                    "Litre bilgisi girilmeden onaylanamaz!"
                )
            kayit.durum = 'onaylandi'

    def action_iptal(self):
        # İptal et — hakediş hesabına dahil edilmez
        # Kayıt silinmez — audit trail korunur
        for kayit in self:
            kayit.durum = 'iptal'