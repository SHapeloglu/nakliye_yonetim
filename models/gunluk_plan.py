from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeGunlukPlan(models.Model):
    _name = 'nakliye.gunluk.plan'
    _description = 'Günlük Nakliye Planı'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Plan tarihi ve şantiye bilgisi
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
    saha_id = fields.Many2one(
        'nakliye.saha',
        string='Saha',
        required=True,
        tracking=True,
    # domain → sadece seçili şantiyenin sahaları gelir
    # santiye_id değişince saha listesi otomatik güncellenir
        domain="[('santiye_id', '=', santiye_id)]"
        )

    # Planı oluşturan formen
    # TODO Faz 3: hr.employee [calisma_tipi=formen] ile kısıtlanacak
    formen_id = fields.Many2one(
        'res.users',
        string='Formen',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )

    # Plan durumu — iş akışı bu alan üzerinden yönetilir
    durum = fields.Selection([
        ('taslak', 'Taslak'),
        ('onaylandi', 'Onaylandı'),
        ('kapali', 'Kapalı'),
    ], string='Durum', default='taslak', tracking=True)

    # Plan satırları — her araç için ayrı satır
    satir_ids = fields.One2many(
        'nakliye.plan.satir',
        'plan_id',
        string='Plan Satırları'
    )

    def action_onayla(self):
        # Taslak → Onaylandı geçişi
        # Satır yoksa onaylanamaz
        for kayit in self:
            if not kayit.satir_ids:
                raise ValidationError("Plan satırı olmadan onaylanamaz!")
            kayit.durum = 'onaylandi'

    def action_kapat(self):
        # Onaylandı → Kapalı geçişi
        for kayit in self:
            kayit.durum = 'kapali'

class NakliyePlanSatir(models.Model):
    _name = 'nakliye.plan.satir'
    _description = 'Günlük Plan Satırı'

    # Bağlı plan — silinince satırlar da silinir
    plan_id = fields.Many2one(
        'nakliye.gunluk.plan',
        string='Plan',
        required=True,
        ondelete='cascade'
    )

    # Araç ve şoför bilgisi
    # TODO Faz 3: domain — sadece aktif nakliyecilerin araçları
    arac_id = fields.Many2one(
        'res.partner',
        string='Araç',
        required=True,
        # domain → sadece seçili nakliyecinin alt carileri gelir
        domain="[('parent_id.supplier_rank', '>', 0)]"
    )
    sofor_id = fields.Many2one(
        'res.partner',
        string='Şoför',
         # domain → sadece seçili aracın şoförleri gelir
        domain="[('parent_id', '=', arac_id)]"
    )

    # Görev tipi — döküm mu, malzeme taşıma mı
    gorev_tipi = fields.Selection([
        ('moloz', 'Moloz'),
        ('dokum', 'Döküm'),
        ('micir', 'Mıcır'),
        ('kum', 'Kum'),
        ('stabilize', 'Stabilize'),
        ], string='Görev Tipi', required=True)

    # Lokasyonlar — görev tipine göre doldurulur
    kazi_yeri = fields.Char(string='Kazı Yeri')
    dokum_yeri_id = fields.Many2one(
        'res.partner',
        string='Döküm Yeri'
        # TODO Faz 3: domain — döküm yeri tipindeki lokasyonlar
    )
    tedarikci_id = fields.Many2one(
        'res.partner',
        string='Tedarikçi'
        # TODO Faz 3: domain — tedarikçi tipindeki lokasyonlar
    )

    # Planlanan km bilgisi — döküm fişiyle karşılaştırılacak
    plan_km_gidis = fields.Float(string='Gidiş Km')
    plan_km_donus = fields.Float(string='Dönüş Km')

    # Sefer tipi — km hesabını etkiler
    sefer_tipi = fields.Selection([
        ('dolu_bos', 'Dolu-Boş'),
        ('bos_dolu', 'Boş-Dolu'),
        ('dolu_dolu', 'Dolu-Dolu'),
    ], string='Sefer Tipi', required=True, default='dolu_bos')

    notlar = fields.Text(string='Notlar')