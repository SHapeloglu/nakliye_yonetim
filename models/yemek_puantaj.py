from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeYemekPuantaj(models.Model):
    _name = 'nakliye.yemek.puantaj'
    _description = 'Günlük Yemek Puantajı'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tarih = fields.Date(
        string='Tarih',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True,
        tracking=True
    )

    # Bağlı yemek planı — şantiye seçilince aktif plan otomatik gelir
    plan_id = fields.Many2one(
        'nakliye.yemek.plan',
        string='Yemek Planı',
        tracking=True,
        domain="[('santiye_id', '=', santiye_id), ('aktif', '=', True)]"
    )

    yemek_firmasi_id = fields.Many2one(
        'res.partner',
        string='Yemek Firması',
        tracking=True
    )

    # Puantaj satırları — plandan otomatik kopyalanır
    satir_ids = fields.One2many(
        'nakliye.yemek.puantaj.satir',
        'puantaj_id',
        string='Puantaj Satırları'
    )

    # Özet sayılar — hesaplanmış alanlar
    toplam_personel = fields.Integer(
        string='Toplam Personel',
        compute='_compute_toplamlar',
        store=True
    )
    toplam_taseron_sofor = fields.Integer(
        string='Toplam Taşeron Şoför',
        compute='_compute_toplamlar',
        store=True
    )
    toplam_taseron_isci = fields.Integer(
        string='Toplam Taşeron İşçi',
        compute='_compute_toplamlar',
        store=True
    )
    toplam_yemek = fields.Integer(
        string='Toplam Yemek',
        compute='_compute_toplamlar',
        store=True
    )
    toplam_tutar = fields.Float(
        string='Toplam Tutar (TL)',
        compute='_compute_toplamlar',
        store=True
    )

    durum = fields.Selection([
        ('taslak', 'Taslak'),
        ('onaylandi', 'Onaylandı'),
        ('iptal', 'İptal'),
    ], string='Durum', default='taslak', tracking=True)

    notlar = fields.Text(string='Notlar')

    @api.depends('satir_ids', 'satir_ids.adet', 'satir_ids.yemek_bedeli', 'satir_ids.satir_tipi')
    def _compute_toplamlar(self):
        for kayit in self:
            personel_satirlar = kayit.satir_ids.filtered(lambda s: s.satir_tipi == 'personel')
            sofor_satirlar = kayit.satir_ids.filtered(lambda s: s.satir_tipi == 'taseron_sofor')
            isci_satirlar = kayit.satir_ids.filtered(lambda s: s.satir_tipi == 'taseron_isci')

            kayit.toplam_personel = sum(personel_satirlar.mapped('adet'))
            kayit.toplam_taseron_sofor = sum(sofor_satirlar.mapped('adet'))
            kayit.toplam_taseron_isci = sum(isci_satirlar.mapped('adet'))
            kayit.toplam_yemek = sum(kayit.satir_ids.mapped('adet'))
            kayit.toplam_tutar = sum(kayit.satir_ids.mapped(lambda s: s.adet * s.yemek_bedeli))

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id:
            satirlar = []
            for plan_satir in self.plan_id.satir_ids:
                satirlar.append((0, 0, {
                    'satir_tipi': plan_satir.satir_tipi,
                    'isci_id': plan_satir.isci_id.id,
                    'personel_id': plan_satir.personel_id.id,
                    'nakliye_firma_id': plan_satir.nakliye_firma_id.id,
                    'arac_id': plan_satir.arac_id.id,
                    'sofor_adi': plan_satir.sofor_adi,
                    'taseron_firma_id': plan_satir.taseron_firma_id.id,
                    'taseron_isci_id': plan_satir.taseron_isci_id.id,
                    'adet': plan_satir.adet,
                    'yemek_bedeli': self.env['nakliye.ayarlar'].get_ayarlar().yemek_bedeli,
                }))
            self.satir_ids = satirlar

    def action_onayla(self):
        # Taslak → Onaylandı
        for kayit in self:
            if not kayit.satir_ids:
                raise ValidationError("Puantaj satırı olmadan onaylanamaz!")
            kayit.durum = 'onaylandi'

    def action_iptal(self):
        # İptal et
        for kayit in self:
            kayit.durum = 'iptal'


class NakliyeYemekPuantajSatir(models.Model):
    _name = 'nakliye.yemek.puantaj.satir'
    _description = 'Yemek Puantaj Satırı'

    puantaj_id = fields.Many2one(
        'nakliye.yemek.puantaj',
        string='Puantaj',
        required=True,
        ondelete='cascade'
    )

    # 4 tip
    satir_tipi = fields.Selection([
        ('firma_isci', 'Firma İçi İşçi'),
        ('personel', 'Personel'),
        ('taseron_nakliye', 'Taşeron Nakliye'),
        ('taseron_isci', 'Taşeron İşçi'),
    ], string='Tip', required=True, default='personel')

    # Firma içi işçi
    isci_id = fields.Many2one(
        'hr.employee',
        string='İşçi',
        domain="[('calisma_tipi', '=', 'isci')]"
    )

    # Personel
    personel_id = fields.Many2one(
        'hr.employee',
        string='Personel',
        domain="[('calisma_tipi', 'in', ['personel', 'formen', 'yonetici_formen', 'santiye_sefi', 'santiye_muhasebecisi', 'muhasebe_muduru'])]"
    )

    # Taşeron nakliye — önce firma, sonra araç
    nakliye_firma_id = fields.Many2one(
        'res.partner',
        string='Nakliye Firması',
        domain="[('child_ids.nakliye_araci', '=', True)]"
    )
    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        domain="[('parent_id', '=', nakliye_firma_id), ('nakliye_araci', '=', True)]"
    )
    sofor_adi = fields.Char(
        string='Şoför',
        compute='_compute_sofor_adi',
        store=True
    )

    # Taşeron işçi — önce firma, sonra işçi
    taseron_firma_id = fields.Many2one(
        'res.partner',
        string='Taşeron Firma',
        domain="[('taseron_isci_firmasi', '=', True)]"
    )
    taseron_isci_id = fields.Many2one(
        'nakliye.taseron.isci',
        string='Taşeron İşçi',
        domain="[('firma_id', '=', taseron_firma_id), ('aktif', '=', True)]"
    )

    # Yemek adedi ve bedeli
    adet = fields.Integer(string='Adet', default=1)
    yemek_bedeli = fields.Float(string='Yemek Bedeli (TL)')
    tutar = fields.Float(
        string='Tutar (TL)',
        compute='_compute_tutar',
        store=True
    )
    notlar = fields.Text(string='Notlar')

    @api.depends('arac_id')
    def _compute_sofor_adi(self):
        for kayit in self:
            kayit.sofor_adi = kayit.arac_id.aktif_sofor or ''

    @api.depends('adet', 'yemek_bedeli')
    def _compute_tutar(self):
        for kayit in self:
            kayit.tutar = kayit.adet * kayit.yemek_bedeli