from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class NakliyeHakedis(models.Model):
    _name = 'nakliye.hakedis'
    _description = 'Nakliyeci Hakediş'
    # mail.thread → chatter ve tracking desteği
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Hakediş dönemi
    donem_baslangic = fields.Date(
        string='Dönem Başlangıç',
        required=True,
        tracking=True
    )
    donem_bitis = fields.Date(
        string='Dönem Bitiş',
        required=True,
        tracking=True
    )

    # Hakediş tarafları
    nakliyeci_id = fields.Many2one(
        'res.partner',
        string='Nakliyeci',
        required=True,
        tracking=True
    )
    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        required=True,
        # domain → sadece seçili nakliyecinin alt carileri gelir
        domain="[('parent_id', '=', nakliyeci_id)]"
    )
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True,
        tracking=True
    )

    # Hakediş satırları — wizard tarafından oluşturulur
    satir_ids = fields.One2many(
        'nakliye.hakedis.satir',
        'hakedis_id',
        string='Hakediş Satırları'
    )

    # Özet tutarlar — hesaplanmış alanlar
    # @api.depends → satırlar değişince yeniden hesaplanır
    toplam_km = fields.Float(
        string='Toplam Km',
        compute='_compute_toplamlar',
        store=True
    )
    brut_tutar = fields.Float(
        string='Brüt Tutar (TL)',
        compute='_compute_toplamlar',
        store=True
    )
    tevkifat_tutari = fields.Float(
        string='Tevkifat Tutarı (TL)',
        compute='_compute_toplamlar',
        store=True
    )
    net_tutar = fields.Float(
        string='Net Tutar (TL)',
        compute='_compute_toplamlar',
        store=True
    )

    # Tevkifat oranı — fiscal position'dan gelir
    # Faz 9'da sistem ayarlarından otomatik gelecek
    tevkifat_orani = fields.Float(
        string='Tevkifat Oranı (%)',
        tracking=True
    )

    # Hakediş durumu — onay akışı
    durum = fields.Selection([
        ('taslak', 'Taslak'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('odendi', 'Ödendi'),
        ('iptal', 'İptal'),
    ], string='Durum', default='taslak', tracking=True)

    notlar = fields.Text(string='Notlar')

    @api.depends(
        'satir_ids',
        'satir_ids.tutar',
        'tevkifat_orani'
    )
    def _compute_toplamlar(self):
        for kayit in self:
            # Toplam km — tüm satırların km toplamı
            kayit.toplam_km = sum(kayit.satir_ids.mapped('toplam_km'))
            # Brüt tutar — tüm satırların tutar toplamı
            kayit.brut_tutar = sum(kayit.satir_ids.mapped('tutar'))
            # Tevkifat tutarı — brüt × oran / 100
            kayit.tevkifat_tutari = (
                kayit.brut_tutar * kayit.tevkifat_orani / 100
            )
            # Net tutar — brüt - tevkifat
            kayit.net_tutar = kayit.brut_tutar - kayit.tevkifat_tutari

    def action_onaya_gonder(self):
        # Taslak → Onay Bekliyor
        for kayit in self:
            if not kayit.satir_ids:
                raise ValidationError(
                    "Satır olmadan onaya gönderilemez!"
                )
            kayit.durum = 'onay_bekliyor'

    def action_onayla(self):
        # Onay Bekliyor → Onaylandı
        for kayit in self:
            kayit.durum = 'onaylandi'

    def action_odendi(self):
        # Onaylandı → Ödendi
        for kayit in self:
            kayit.durum = 'odendi'

    def action_iptal(self):
        # İptal et
        for kayit in self:
            kayit.durum = 'iptal'
    @api.model
    def action_hakedis_hatirlatma(self):
        from datetime import date, timedelta
        bugun = date.today()

        # Ayarlar modelinden hatırlatma gün sayısını al
        ayarlar = self.env['nakliye.ayarlar'].get_ayarlar()
        hatirlatma_gun = ayarlar.hakedis_hatirlatma_gun or 3
        bekleme_tarihi = bugun - timedelta(days=hatirlatma_gun)

        onay_bekleyenler = self.search([
            ('durum', '=', 'onay_bekliyor'),
            ('write_date', '<=', bekleme_tarihi),
        ])

        for hakedis in onay_bekleyenler:
            hakedis.message_post(
                body=f"⚠️ Bu hakediş {hatirlatma_gun} günden fazladır onay bekliyor!",
                subject="Hakediş Onay Hatırlatması",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

class NakliyeHakedisSatir(models.Model):
    _name = 'nakliye.hakedis.satir'
    _description = 'Hakediş Satırı'

    # Bağlı hakediş — silinince satırlar da silinir
    hakedis_id = fields.Many2one(
        'nakliye.hakedis',
        string='Hakediş',
        required=True,
        ondelete='cascade'
    )

    # Satır tipi — hangi fiş tipinden geldiği
    satir_tipi = fields.Selection([
        ('moloz', 'Moloz'),
        ('dokum', 'Döküm'),
        ('micir', 'Mıcır'),
        ('kum', 'Kum'),
        ('stabilize', 'Stabilize'),
        ], string='Satır Tipi', required=True)

    # Bağlı döküm fişi
    dokum_fisi_id = fields.Many2one(
        'nakliye.dokum.fisi',
        string='Döküm Fişi'
    )

    # Km bilgileri
    gidis_km = fields.Float(string='Gidiş Km')
    donus_km = fields.Float(string='Dönüş Km')
    toplam_km = fields.Float(
        string='Toplam Km',
        compute='_compute_toplam_km',
        store=True
    )

    # Birim fiyatlar — sözleşmeden gelir
    km_fiyat_dolu = fields.Float(string='Dolu Km Fiyatı (TL)')
    km_fiyat_bos = fields.Float(string='Boş Km Fiyatı (TL)')

    # Satır tutarı — hesaplanmış
    tutar = fields.Float(
        string='Tutar (TL)',
        compute='_compute_tutar',
        store=True
    )

    tarih = fields.Date(string='Tarih')
    notlar = fields.Text(string='Notlar')

    @api.depends('gidis_km', 'donus_km')
    def _compute_toplam_km(self):
        for kayit in self:
            kayit.toplam_km = kayit.gidis_km + kayit.donus_km

    @api.depends('gidis_km', 'donus_km', 'km_fiyat_dolu', 'km_fiyat_bos')
    def _compute_tutar(self):
        for kayit in self:
            # Tutar = (gidiş km × dolu fiyat) + (dönüş km × boş fiyat)
            kayit.tutar = (
                kayit.gidis_km * kayit.km_fiyat_dolu +
                kayit.donus_km * kayit.km_fiyat_bos
            )