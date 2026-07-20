from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeHakedisWizard(models.TransientModel):
    _name = 'nakliye.hakedis.wizard'
    _description = 'Hakediş Oluşturma Sihirbazı'

    # Muhasebeci bu bilgileri girerek hakedişi hesaplar
    donem_baslangic = fields.Date(
        string='Dönem Başlangıç',
        required=True
    )
    donem_bitis = fields.Date(
        string='Dönem Bitiş',
        required=True
    )
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True
    )
    nakliyeci_id = fields.Many2one(
        'res.partner',
        string='Nakliyeci',
        required=True
    )
    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        required=True,
        # domain → sadece seçili nakliyecinin alt carileri gelir
        domain="[('parent_id', '=', nakliyeci_id)]"
    )
    tevkifat_orani = fields.Float(
        string='Tevkifat Oranı (%)',
        default=0.0
    )

    @api.constrains('donem_baslangic', 'donem_bitis')
    def _check_donem(self):
        for kayit in self:
            # Bitiş tarihi başlangıçtan önce olamaz
            if kayit.donem_bitis < kayit.donem_baslangic:
                raise ValidationError(
                    "Dönem bitiş tarihi başlangıç tarihinden önce olamaz!"
                )

    def action_hakedis_olustur(self):
        # Ana metod — tüm onaylı fişleri toplayıp hakediş oluşturur
        self.ensure_one()

        # 1. Bu araç ve şantiye için aktif sözleşmeyi bul
        sozlesme = self.env['nakliye.sozlesme'].search([
            ('arac_id', '=', self.arac_id.id),
            ('santiye_id', '=', self.santiye_id.id),
            ('aktif', '=', True),
        ], limit=1)
        # Debug — log'a yaz
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Aranan arac_id: {self.arac_id.id}, santiye_id: {self.santiye_id.id}")
        _logger.info(f"Bulunan sözleşme: {sozlesme}")

        if not sozlesme:
            raise ValidationError(
                f"{self.arac_id.name} aracı için "
                f"{self.santiye_id.name} şantiyesinde aktif sözleşme bulunamadı!"
            )

        # 2. Dönem içindeki onaylı döküm fişlerini bul
        dokum_fisler = self.env['nakliye.dokum.fisi'].search([
            ('arac_id', '=', self.arac_id.id),
            ('santiye_id', '=', self.santiye_id.id),
            ('tarih', '>=', self.donem_baslangic),
            ('tarih', '<=', self.donem_bitis),
            ('durum', '=', 'onaylandi'),
        ])

        if not dokum_fisler:
            raise ValidationError(
                "Seçilen dönemde onaylı döküm fişi bulunamadı!"
            )

        # 3. Hakediş satırlarını oluştur
        satir_vals = []
        for fis in dokum_fisler:
            # Fişin görev tipine göre sözleşmeden doğru fiyatı bul
            sozlesme_satir = sozlesme.satir_ids.filtered(
                lambda s: s.lokasyon_tipi == fis.plan_satir_id.gorev_tipi
            )
            # Fiyat bulunamazsa sözleşmenin ilk satırını kullan
            if sozlesme_satir:
                km_dolu = sozlesme_satir[0].km_birim_fiyat_dolu
                km_bos = sozlesme_satir[0].km_birim_fiyat_bos
            else:
                km_dolu = 0
                km_bos = 0

            satir_vals.append({
                'tarih': fis.tarih,
                'satir_tipi': fis.plan_satir_id.gorev_tipi,
                'dokum_fisi_id': fis.id,
                'gidis_km': fis.gidis_km,
                'donus_km': fis.donus_km,
                'km_fiyat_dolu': km_dolu,
                'km_fiyat_bos': km_bos,
            })

        # 4. Hakediş kaydını oluştur
        hakedis = self.env['nakliye.hakedis'].create({
            'donem_baslangic': self.donem_baslangic,
            'donem_bitis': self.donem_bitis,
            'nakliyeci_id': self.nakliyeci_id.id,
            'arac_id': self.arac_id.id,
            'santiye_id': self.santiye_id.id,
            'tevkifat_orani': self.tevkifat_orani,
            'satir_ids': [(0, 0, satir) for satir in satir_vals],
        })

        # 5. Oluşturulan hakedişi aç
        # Wizard kapanır, hakediş formu açılır
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hakediş',
            'res_model': 'nakliye.hakedis',
            'res_id': hakedis.id,
            'view_mode': 'form',
            'target': 'current',
        }