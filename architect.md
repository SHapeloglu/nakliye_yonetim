# architect.md — Nakliye Yönetim Mimarisi (Odoo 18)

## Genel Yapı

Standart Odoo modülü (`application: True`), bağımlılıklar: `base, mail, account, hr, fleet, maintenance`. Ayrıntılı alan/kural listesi: **`nakliye_yonetim_spec.md`** (tek doğruluk kaynağı) ve `nakliye_yonetim_analiz.docx`.

```
Tanımlamalar: Şantiye ─┬─ Saha (formen_ids)
                       ├─ Sözleşme (nakliyeci × araç × şantiye, satırlar = fiyatlar)
                       └─ Yemek Planı
Cari (res.partner) ── araç-şoför (nakliye.arac.sofor), taşeron işçi (nakliye.taseron.isci)
Çalışan (hr.employee) ── şantiye ataması (nakliye.employee.santiye)
Operasyon: Günlük Plan (+satır) · Döküm Fişi · Kantar Fişi · Yakıt Fişi · Yemek Puantajı (+satır)
Muhasebe:  Hakediş Wizard ──► Hakediş (+satır) ──► QWeb PDF (report/hakedis_report.xml)
Zimmet:    maintenance.equipment extend
```

## Modeller

| Model | Dosya | Not |
|---|---|---|
| `nakliye.santiye` | `models/santiye.py` | `muhasebeci_ids` → satır bazlı erişim |
| `nakliye.saha` | `models/saha.py` | `formen_ids` (şu an `res.users`) |
| `res.partner` extend, `nakliye.arac.sofor`, `nakliye.taseron.isci` | `models/partner.py` | Nakliyeci / taşeron bilgileri |
| `nakliye.sozlesme`, `nakliye.sozlesme.satir` | `models/sozlesme.py` | Araç+şantiye başına tek aktif sözleşme; fiyat değişince eskisi pasif |
| `hr.employee` extend, `nakliye.employee.santiye` | `models/hr_employee.py`, `employee_santiye.py` | Çalışan başına tek aktif atama |
| `nakliye.gunluk.plan`, `nakliye.plan.satir` | `models/gunluk_plan.py` | Günlük sefer planı |
| `nakliye.dokum.fisi` | `models/dokum_fisi.py` | Döküm; km validasyonu |
| `nakliye.kantar.fisi` | `models/kantar_fisi.py` | Tonaj; araç yük haddi aşımı → nakliyeci sorumlu |
| `nakliye.yakit.fisi` | `models/yakit_fisi.py` | Yakıt |
| `nakliye.yemek.plan`(+satır), `nakliye.yemek.puantaj`(+satır) | `models/yemek_*.py` | Şantiyede tek aktif yemek planı |
| `nakliye.hakedis`, `nakliye.hakedis.satir` | `models/hakedis.py` | Durumlar: taslak → onaya gönder → onay → ödendi / iptal; tevkifat fiscal position ile |
| `nakliye.hakedis.wizard` | `wizard/hakedis_wizard.py` | Dönem + nakliyeci için hakediş üretimi |
| `nakliye.ayarlar` | `models/ayarlar.py` | Tevkifat oranı vb. |
| `maintenance.equipment` extend | `models/equipment.py` | Zimmet |

## Güvenlik

Gruplar (`security/groups.xml`): Formen → Yönetici Formen → Şantiye Muhasebecisi → Muhasebe Müdürü → Yönetim → Admin.
Satır kuralları (`security/ir_rule.xml`): formen `saha_id.formen_ids` ile, şantiye muhasebecisi `santiye_id.muhasebeci_ids` ile sınırlı; muhasebe müdürü ve admin için kural yok.

## Zamanlanmış Görevler (`data/cron.xml`)

- Günlük: `nakliye.sozlesme.action_bitis_kontrol()` — sözleşme bitiş kontrolü.
- Günlük: `nakliye.hakedis.action_hakedis_hatirlatma()` — onay bekleyen hakediş hatırlatması.

## İş Kuralları (spec §6)

Şantiye izolasyonu · tek aktif sözleşme (araç+şantiye) · tek aktif yemek planı (şantiye) · tek aktif atama (çalışan) · tonaj aşımında nakliyeci sorumlu · tevkifat fiscal position ile · fiyat değişiminde eski sözleşme pasif, geçmiş hakediş korunur · negatif/0 km onayı engelli.

## Odoo 17 sürümünden farklar

- Görünümlerde `<tree>` → `<list>`, aksiyonlara `path` (ör. `nakliye-santiye`).
- `nakliye.arac.sofor.sofor_adi`, `nakliye.taseron.isci.isci_adi` zorunlu.
- 2026-07-20 güncellemeleri (README, partner/görünüm düzeltmeleri).

## Mimari Kararlar

- **Extend önce**: sıfırdan model yerine standart Odoo modelleri genişletildi.
- **Spec önce**: `nakliye_yonetim_spec.md` kodla birlikte tutuluyor.
- **Satır bazlı izolasyon `ir.rule` ile**; muhasebe müdürü ve admin kısıtsız.
- **Sözleşme geçmişi korunur**: fiyat değişikliği yeni sözleşme açar.
