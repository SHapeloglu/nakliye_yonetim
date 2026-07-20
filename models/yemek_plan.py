from odoo import models, fields, api
from odoo.exceptions import ValidationError

class NakliyeYemekPlan(models.Model):
    _name = 'nakliye.yemek.plan'
    _description = 'Yemek Planı'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Adı', required=True, tracking=True)
    santiye_id = fields.Many2one(
        'nakliye.santiye',
        string='Şantiye',
        required=True,
        tracking=True
    )
    # Plan geçerlilik tarihleri
    baslangic_tarihi = fields.Date(
        string='Başlangıç Tarihi',
        required=True,
        tracking=True
    )
    bitis_tarihi = fields.Date(
        string='Bitiş Tarihi',
        tracking=True
    )
    # Aktif plan — günlük puantaj bu planı çeker
    # Bitiş tarihi dolunca False yapılır
    aktif = fields.Boolean(string='Aktif', default=True, tracking=True)

    # Plan satırları
    satir_ids = fields.One2many(
        'nakliye.yemek.plan.satir',
        'plan_id',
        string='Plan Satırları'
    )

    @api.constrains('aktif', 'santiye_id')
    def _check_tek_aktif_plan(self):
        # Bir şantiyede aynı anda sadece bir aktif plan olabilir
        for kayit in self:
            if kayit.aktif:
                duplicate = self.search([
                    ('santiye_id', '=', kayit.santiye_id.id),
                    ('aktif', '=', True),
                    ('id', '!=', kayit.id)
                ])
                if duplicate:
                    raise ValidationError(
                        f"{kayit.santiye_id.name} şantiyesi için "
                        f"zaten aktif bir yemek planı var!"
                    )

    def action_dublike(self):
        # Mevcut planı dublike et — yeni plan için kullan
        # Eski planın bitiş tarihini bugün yap, pasife al
        self.ensure_one()
        from datetime import date
        self.write({
            'bitis_tarihi': date.today(),
            'aktif': False,
        })
        # Yeni plan oluştur — aynı satırlarla
        yeni_plan = self.copy({
            'name': f"{self.name} (Yeni)",
            'baslangic_tarihi': date.today(),
            'bitis_tarihi': False,
            'aktif': True,
        })
        # Yeni planı aç
        return {
            'type': 'ir.actions.act_window',
            'name': 'Yemek Planı',
            'res_model': 'nakliye.yemek.plan',
            'res_id': yeni_plan.id,
            'view_mode': 'form',
            'target': 'current',
        }

class NakliyeYemekPlanSatir(models.Model):
    _name = 'nakliye.yemek.plan.satir'
    _description = 'Yemek Planı Satırı'

    plan_id = fields.Many2one(
        'nakliye.yemek.plan',
        string='Plan',
        required=True,
        ondelete='cascade'
    )

    # 4 tip — firma içi işçi, personel, taşeron nakliye, taşeron işçi
    satir_tipi = fields.Selection([
        ('firma_isci', 'Firma İçi İşçi'),
        ('personel', 'Personel'),
        ('taseron_nakliye', 'Taşeron Nakliye'),
        ('taseron_isci', 'Taşeron İşçi'),
    ], string='Tip', required=True, default='personel')

    # Firma içi işçi için — hr.employee, calisma_tipi=isci
    isci_id = fields.Many2one(
        'hr.employee',
        string='İşçi',
        domain="[('calisma_tipi', '=', 'isci')]"
    )

    # Personel için — hr.employee, formen/şef/muhasebeci vs.
    personel_id = fields.Many2one(
        'hr.employee',
        string='Personel',
        domain="[('calisma_tipi', 'in', ['personel', 'formen', 'yonetici_formen', 'santiye_sefi', 'santiye_muhasebecisi', 'muhasebe_muduru'])]"
    )

    # Taşeron nakliye — önce firma, sonra o firmanın araçları
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
    # Aktif şoför — araç seçilince computed field ile gelir
    sofor_adi = fields.Char(
        string='Şoför',
        compute='_compute_sofor_adi',
        store=True
    )

    # Taşeron işçi — önce firma, sonra o firmanın aktif işçileri
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

    # Günlük yemek adedi — varsayılan 1
    adet = fields.Integer(string='Günlük Yemek Adedi', default=1)
    notlar = fields.Text(string='Notlar')

    @api.depends('arac_id')
    def _compute_sofor_adi(self):
        for kayit in self:
            # Araç seçilince aktif şoförü getir
            kayit.sofor_adi = kayit.arac_id.aktif_sofor or ''