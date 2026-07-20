from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeDokumFisi(models.Model):
    _name = 'nakliye.dokum.fisi'
    _description = 'Döküm Fişi'
    # mail.thread → chatter ve tracking desteği
    # mail.activity.mixin → aktivite (hatırlatma) desteği
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Bağlı plan satırı — hangi araç, hangi görev tipinde çalışıyor
    plan_satir_id = fields.Many2one(
        'nakliye.plan.satir',
        string='Plan Satırı',
        required=True,
        tracking=True
    )

    # related → plan satırından otomatik gelen bilgiler
    # store=True → veritabanına kaydedilir, raporlarda ve filtrelerde kullanılır
    # store=False olsaydı domain ve arama yapılamazdı
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        related='plan_satir_id.plan_id.santiye_id',
        store=True
    )
    saha_id = fields.Many2one(
        'nakliye.saha',
        string='Saha',
        related='plan_satir_id.plan_id.saha_id',
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

    # Fiş bilgileri — formen tarafından sahada girilir
    gidis_km = fields.Float(string='Gidiş Km', required=True, tracking=True)
    donus_km = fields.Float(string='Dönüş Km', required=True, tracking=True)

    # Hesaplanmış alan — gidis_km + donus_km
    # @api.depends → bu iki alan değişince otomatik yeniden hesaplanır
    # store=True → hakediş hesabında SQL ile sorgulanabilir
    toplam_km = fields.Float(
        string='Toplam Km',
        compute='_compute_toplam_km',
        store=True
    )

    # Döküm yeri — plan satırından farklı olabilir
    # Örnek: plan Döküm A'ya göre yapıldı ama fiilen Döküm B'ye gidildi
    dokum_yeri_id = fields.Many2one(
        'res.partner',
        string='Döküm Yeri',
        tracking=True
    )

    # Fiş durumu — iş akışı bu alan üzerinden yönetilir
    # taslak → formen girdi, henüz onaylanmadı
    # onaylandi → muhasebeci onayladı, hakediş hesabına dahil edilir
    # iptal → yanlış girilmiş, hakediş dışında tutulur
    durum = fields.Selection([
        ('taslak', 'Taslak'),
        ('onaylandi', 'Onaylandı'),
        ('iptal', 'İptal'),
    ], string='Durum', default='taslak', tracking=True)

    notlar = fields.Text(string='Notlar')

    @api.depends('gidis_km', 'donus_km')
    def _compute_toplam_km(self):
        # gidis_km veya donus_km değiştiğinde otomatik çalışır
        # toplam_km kullanıcı tarafından girilemez — sistem hesaplar
        for kayit in self:
            kayit.toplam_km = kayit.gidis_km + kayit.donus_km

    @api.constrains('gidis_km', 'donus_km')
    def _check_km(self):
        # Kayıt kaydedilmeden önce çalışır
        # Negatif km iş kuralına aykırı — ValidationError fırlatır
        for kayit in self:
            if kayit.gidis_km < 0 or kayit.donus_km < 0:
                raise ValidationError("Km değeri negatif olamaz!")

    def action_onayla(self):
        # Taslak → Onaylandı geçişi
        # Km girilmemişse onaylanamaz — hakediş hesabı bozulur
        for kayit in self:
            if kayit.toplam_km == 0:
                raise ValidationError("Km bilgisi girilmeden onaylanamaz!")
            kayit.durum = 'onaylandi'

    def action_iptal(self):
        # Onaylandı → İptal geçişi
        # İptal edilen fiş hakediş hesabına dahil edilmez
        # Kayıt silinmez — audit trail korunur
        for kayit in self:
            kayit.durum = 'iptal'