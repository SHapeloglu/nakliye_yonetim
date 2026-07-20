from odoo import models, fields, api

class NakliyeAyarlar(models.TransientModel):
    _name = 'nakliye.ayarlar'
    _description = 'Nakliye Yönetim Ayarları'
    # TransientModel — ayarlar tek kayıt olarak tutulur
    # res.config.settings gibi davranır

    # Tevkifat oranı — kanunla belirlenir, muhasebe müdürü günceller
    # Geçmiş hakedişler güncelleme öncesi oran üzerinden korunur
    # çünkü hakediş oluşturulurken oran hakedişe kopyalanır
    tevkifat_orani = fields.Float(
        string='Tevkifat Oranı (%)',
        default=3.0
    )

    # Yemek bedeli — günlük varsayılan yemek bedeli
    # Yemek puantaj satırlarına otomatik gelir
    yemek_bedeli = fields.Float(
        string='Günlük Yemek Bedeli (TL)',
        default=0.0
    )

    # Sözleşme bitiş uyarı süresi — kaç gün önceden uyarı verilsin
    sozlesme_uyari_gun = fields.Integer(
        string='Sözleşme Bitiş Uyarı Süresi (Gün)',
        default=30
    )

    # Hakediş onay bekleme süresi — kaç gün sonra hatırlatma yapılsın
    hakedis_hatirlatma_gun = fields.Integer(
        string='Hakediş Hatırlatma Süresi (Gün)',
        default=3
    )

    @api.model
    def get_ayarlar(self):
        # Mevcut ayarları getir — yoksa yeni oluştur
        ayarlar = self.search([], limit=1)
        if not ayarlar:
            ayarlar = self.create({})
        return ayarlar

    def kaydet(self):
        # Ayarları kaydet — wizard gibi çalışır
        return {'type': 'ir.actions.act_window_close'}