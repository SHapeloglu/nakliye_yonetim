from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Çalışma tipi — tüm domain filtrelerinin temeli
    # İşçiler Odoo'ya giriş yapmaz, formen ve personel yapar
    calisma_tipi = fields.Selection([
        ('isci', 'İşçi'),
        ('personel', 'Personel'),
        ('formen', 'Formen'),
        ('yonetici_formen', 'Yönetici Formen'),
        ('santiye_sefi', 'Şantiye Şefi'),
        ('santiye_muhasebecisi', 'Şantiye Muhasebecisi'),
        ('muhasebe_muduru', 'Muhasebe Müdürü'),
    ], string='Çalışma Tipi', required=True, tracking=True)
    # required=True → çalışma tipi girilmeden kayıt açılamaz
    # tracking=True → değişiklikler chatter'a loglanır

    # Odoo kullanıcı bağlantısı
    # İşçiler için boş — formen ve personel için zorunlu
    # Şoför için opsiyonel
    odoo_user_id = fields.Many2one(
        'res.users',
        string='Odoo Kullanıcısı',
        tracking=True
    )

    # Şantiye atama geçmişi — nakliye.employee.santiye modelinden One2many
    santiye_atama_ids = fields.One2many(
        'nakliye.employee.santiye',
        'employee_id',
        string='Şantiye Atamaları'
    )

    # Aktif şantiye — atama geçmişinden hesaplanır
    # store=True → veritabanına kaydedilir, domain filtresi ve ir.rule'da kullanılabilir
    # store=False olsaydı arama/filtreleme yapılamazdı
    aktif_santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Aktif Şantiye',
        compute='_compute_aktif_santiye',
        store=True
    )

    # @api.depends → hangi alanlar değişince bu metod yeniden çalışacak
    # santiye_atama_ids, aktif veya bitis_tarihi değişince yeniden hesapla
    @api.depends('santiye_atama_ids', 'santiye_atama_ids.aktif',
                 'santiye_atama_ids.bitis_tarihi')
    def _compute_aktif_santiye(self):
        for kayit in self:
            # filtered(lambda) → listeden koşula uyanları getir
            # a.aktif=True VE a.bitis_tarihi boş → şu an aktif atama
            aktif_atama = kayit.santiye_atama_ids.filtered(
                lambda a: a.aktif and not a.bitis_tarihi
            )
            # [:1] → teoride tek atama olmalı ama veri tutarsızlığına karşı
            # ilk kaydı al — birden fazla gelirse hata verme
            # if aktif_atama else False → atama yoksa şantiyeyi boş bırak
            kayit.aktif_santiye_id = aktif_atama[:1].santiye_id if aktif_atama else False