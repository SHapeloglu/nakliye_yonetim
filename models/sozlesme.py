from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class NakliyeSozlesme(models.Model):
    _name = 'nakliye.sozlesme'
    _description = 'Nakliyeci-Şantiye Sözleşmesi'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    nakliyeci_id = fields.Many2one(
        'res.partner',
        string='Nakliyeci',
        required=True,
        tracking=True
    )
    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        tracking=True,
    # domain → sadece seçili nakliyecinin alt carileri gelir
    # parent_id = nakliyeci seçilince araç listesi filtreler
        domain="[('parent_id', '=', nakliyeci_id)]"
    )
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True,
        tracking=True
    )
    baslangic_tarihi = fields.Date(string='Başlangıç Tarihi', required=True)
    bitis_tarihi = fields.Date(string='Bitiş Tarihi')
    notlar = fields.Text(string='Notlar')
    aktif = fields.Boolean(string='Aktif', default=True, tracking=True)

    # Lokasyon bazlı fiyat satırları
    satir_ids = fields.One2many(
        'nakliye.sozlesme.satir',
        'sozlesme_id',
        string='Fiyat Satırları'
    )

    @api.constrains('arac_id', 'santiye_id', 'aktif')
    def _check_unique_aktif_sozlesme(self):
        # Aynı araç için aynı şantiyede aynı anda sadece bir aktif sözleşme olabilir
        # Fiyat değişince eski sözleşme pasife alınır, yeni sözleşme açılır
        # Geçmiş hakedişler eski fiyatla korunur
        for kayit in self:
            if kayit.aktif:
                duplicate = self.search([
                    ('arac_id', '=', kayit.arac_id.id),
                    ('santiye_id', '=', kayit.santiye_id.id),
                    ('aktif', '=', True),
                    ('id', '!=', kayit.id)
                ])
                if duplicate:
                    raise ValidationError(
                        f"{kayit.arac_id.name} aracı için "
                        f"{kayit.santiye_id.name} şantiyesinde "
                        f"zaten aktif bir sözleşme var!"
                    )
                
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
class NakliyeSozmeSatir(models.Model):
    _name = 'nakliye.sozlesme.satir'
    _description = 'Sözleşme Fiyat Satırı'

    sozlesme_id = fields.Many2one(
        'nakliye.sozlesme',
        string='Sözleşme',
        required=True,
        ondelete='cascade'
    )
    lokasyon_tipi = fields.Selection([
        ('moloz', 'Moloz'),
        ('dokum', 'Döküm Yeri'),
        ('micir', 'Mıcır Ocağı'),
        ('kum', 'Kum Ocağı'),
        ('stabilize', 'Stabilize Ocağı'),
        ], string='Lokasyon Tipi', required=True)

    lokasyon_id = fields.Many2one(
        'res.partner',
        string='Lokasyon',
        # TODO Faz 3: lokasyon tipine göre filtrelenecek
    )
    km_birim_fiyat_dolu = fields.Float(string='Dolu Sefer (TL/km)', required=True)
    km_birim_fiyat_bos = fields.Float(string='Boş Sefer (TL/km)', required=True)
    notlar = fields.Text(string='Notlar')