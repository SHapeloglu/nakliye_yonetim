from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Nakliye aracı tiki — işaretlenince araç alanları görünür
    nakliye_araci = fields.Boolean(string='Nakliye Aracı', default=False)

    # Araç bilgileri — sadece nakliye_araci=True ise kullanılır
    plaka = fields.Char(string='Plaka')
    kapasite_ton = fields.Float(string='Kapasite (Ton)')
    yuk_haddi_ton = fields.Float(string='Yük Haddi (Ton)')

    # Şoför geçmişi — araç kaydının altında satırlar
    sofor_gecmisi_ids = fields.One2many(
        'nakliye.arac.sofor',
        'arac_id',
        string='Şoför Geçmişi'
    )

    # Aktif şoför — geçmişten hesaplanır
    aktif_sofor = fields.Char(
        string='Aktif Şoför',
        compute='_compute_aktif_sofor',
        store=True
    )

    # Taşeron işçi firması tiki — işaretlenince işçi listesi görünür
    taseron_isci_firmasi = fields.Boolean(
        string='Taşeron İşçi Firması',
        default=False
    )

    # İşçi listesi — taşeron işçi firması için
    isci_listesi_ids = fields.One2many(
        'nakliye.taseron.isci',
        'firma_id',
        string='İşçi Listesi'
    )

    @api.depends('sofor_gecmisi_ids', 'sofor_gecmisi_ids.aktif')
    def _compute_aktif_sofor(self):
        for kayit in self:
            aktif = kayit.sofor_gecmisi_ids.filtered(lambda s: s.aktif)
            kayit.aktif_sofor = aktif[:1].sofor_adi if aktif else ''


class NakliyeAracSofor(models.Model):
    _name = 'nakliye.arac.sofor'
    _description = 'Araç Şoför Geçmişi'

    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        required=True,
        ondelete='cascade'
    )
    sofor_adi = fields.Char(string='Şoför Adı', required=True)
    baslangic_tarihi = fields.Date(string='Başlangıç Tarihi', required=True)
    bitis_tarihi = fields.Date(string='Bitiş Tarihi')
    aktif = fields.Boolean(string='Aktif', default=True)
    notlar = fields.Text(string='Notlar')


class NakliyeTaseronIsci(models.Model):
    _name = 'nakliye.taseron.isci'
    _description = 'Taşeron İşçi Listesi'
    _rec_name = 'isci_adi'  # ← bunu ekleyin

    firma_id = fields.Many2one(
        'res.partner',
        string='Taşeron Firma',
        required=True,
        ondelete='cascade'
    )
    # İşçi adı — bizim personelimiz değil, elle yazılır
    isci_adi = fields.Char(string='İşçi Adı', required=True)
    baslangic_tarihi = fields.Date(string='Başlangıç Tarihi', required=True)
    bitis_tarihi = fields.Date(string='Bitiş Tarihi')
    # Birden fazla işçi aynı anda aktif olabilir
    aktif = fields.Boolean(string='Aktif', default=True)
    notlar = fields.Text(string='Notlar')