from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeKantarFisi(models.Model):
    _name = 'nakliye.kantar.fisi'
    _description = 'Kantar Fişi'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Bağlı plan satırı — hangi araç, hangi görev
    plan_satir_id = fields.Many2one(
        'nakliye.plan.satir',
        string='Plan Satırı',
        required=True,
        tracking=True
    )
    saha_id = fields.Many2one(
        'nakliye.saha',
        string='Saha',
        related='plan_satir_id.plan_id.saha_id',
        store=True
    )

    # Plan satırından otomatik gelen bilgiler
    # related + store=True → veritabanına kaydedilir, filtrelerde kullanılır
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

    # Kantar bilgileri — kum, mıcır, stabilize için
    tedarikci_id = fields.Many2one(
        'res.partner',
        string='Tedarikçi',
        tracking=True
    )

    # Tartı bilgileri
    # Tara = boş araç ağırlığı, Brüt = dolu araç ağırlığı
    tara_kg = fields.Float(string='Tara (kg)', tracking=True)
    brut_kg = fields.Float(string='Brüt (kg)', tracking=True)

    # Net ağırlık — hesaplanmış alan
    # net_kg = brut_kg - tara_kg
    net_kg = fields.Float(
        string='Net (kg)',
        compute='_compute_net_kg',
        store=True
    )
    net_ton = fields.Float(
        string='Net (ton)',
        compute='_compute_net_kg',
        store=True
    )

    # Tonaj aşımı kontrolü — araç kapasitesini aşıyor mu
    # True ise nakliyeci trafik cezasından sorumlu
    tonaj_asimi = fields.Boolean(
        string='Tonaj Aşımı',
        compute='_compute_tonaj_asimi',
        store=True
    )
    asim_miktari_ton = fields.Float(
        string='Aşım Miktarı (ton)',
        compute='_compute_tonaj_asimi',
        store=True
    )

    # Fiş numarası — kantar fişinin orijinal numarası
    fis_no = fields.Char(string='Fiş No', tracking=True)

    # Fiş durumu
    durum = fields.Selection([
        ('taslak', 'Taslak'),
        ('onaylandi', 'Onaylandı'),
        ('iptal', 'İptal'),
    ], string='Durum', default='taslak', tracking=True)

    notlar = fields.Text(string='Notlar')

    @api.depends('brut_kg', 'tara_kg')
    def _compute_net_kg(self):
        for kayit in self:
            # Net ağırlık = brüt - tara
            kayit.net_kg = kayit.brut_kg - kayit.tara_kg
            # Tona çevir — hakediş hesabında ton bazlı kullanılır
            kayit.net_ton = kayit.net_kg / 1000

    @api.depends('net_ton', 'arac_id')
    def _compute_tonaj_asimi(self):
        for kayit in self:
            # Araç yük haddi — res.partner.yuk_haddi_ton
            yuk_haddi = kayit.arac_id.yuk_haddi_ton or 0
            if yuk_haddi and kayit.net_ton > yuk_haddi:
                # Tonaj aşımı var — nakliyeci sorumlu
                kayit.tonaj_asimi = True
                kayit.asim_miktari_ton = kayit.net_ton - yuk_haddi
            else:
                kayit.tonaj_asimi = False
                kayit.asim_miktari_ton = 0

    @api.constrains('brut_kg', 'tara_kg')
    def _check_agirlik(self):
        for kayit in self:
            # Brüt ağırlık tara ağırlığından küçük olamaz
            if kayit.brut_kg < kayit.tara_kg:
                raise ValidationError(
                    "Brüt ağırlık tara ağırlığından küçük olamaz!"
                )
            if kayit.tara_kg < 0 or kayit.brut_kg < 0:
                raise ValidationError("Ağırlık değeri negatif olamaz!")

    def action_onayla(self):
        # Taslak → Onaylandı
        # Net ağırlık sıfırsa onaylanamaz
        for kayit in self:
            if kayit.net_kg <= 0:
                raise ValidationError(
                    "Ağırlık bilgisi girilmeden onaylanamaz!"
                )
            kayit.durum = 'onaylandi'

    def action_iptal(self):
        # İptal et — hakediş hesabına dahil edilmez
        # Kayıt silinmez — audit trail korunur
        for kayit in self:
            kayit.durum = 'iptal'