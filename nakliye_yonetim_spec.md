# Nakliye Yönetim Modülü — Teknik Spesifikasyon

**Modül Adı:** `nakliye_yonetim`  
**Versiyon:** 1.0  
**Odoo Versiyonu:** 18.0  
**Bağımlılıklar:** `base`, `mail`, `account`, `hr`, `fleet`, `maintenance`

---

## 1. GENEL MİMARİ

### 1.1 Yaklaşım
- Mevcut Odoo modülleri **extend** edilir, sıfırdan yazılmaz
- `res.partner` → Nakliyeci, Araç, Döküm Yeri, Tedarikçi
- `hr.employee` → Firma personeli ve işçi takibi
- `maintenance.equipment` → Zimmet takibi
- Şantiye bazlı izolasyon `ir.rule` ile sağlanır

### 1.2 Klasör Yapısı
```
nakliye_yonetim/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── santiye.py
│   ├── saha.py
│   ├── partner.py          (res.partner extend)
│   ├── sozlesme.py
│   ├── employee_santiye.py
│   ├── hr_employee.py      (hr.employee extend)
│   ├── gunluk_plan.py
│   ├── dokum_fisi.py
│   ├── kantar_fisi.py
│   ├── yakit_fisi.py
│   ├── yemek_plan.py
│   ├── yemek_puantaj.py
│   ├── hakedis.py
│   ├── ayarlar.py
│   └── equipment.py        (maintenance.equipment extend)
├── wizard/
│   └── hakedis_wizard.py
├── views/          (her model için ayrı XML)
├── security/
│   ├── groups.xml
│   ├── ir.model.access.csv
│   └── ir_rule.xml
├── report/
│   └── hakedis_report.xml
└── data/
    └── cron.xml
```

---

## 2. VERİ MODELLERİ

### 2.1 Şantiye (`nakliye.santiye`)
Tüm operasyonların üst organizasyon birimi. Toplanma yeri.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `name` | Char | Şantiye adı, zorunlu |
| `kod` | Char | Kısa referans kodu |
| `muhasebeci_ids` | Many2many → `res.users` | Şantiye muhasebecileri |
| `aktif` | Boolean | Pasife alınınca ir.rule devreye girer |

**Özellikler:** `mail.thread`, `mail.activity.mixin`

---

### 2.2 Saha (`nakliye.saha`)
İşin fiilen yapıldığı lokasyon. Şantiyeye bağlı, saha ilerledikçe koordinat güncellenir.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `name` | Char | Saha adı, zorunlu |
| `santiye_id` | Many2one → `nakliye.santiye` | Bağlı şantiye |
| `partner_latitude` | Float | GPS enlemi |
| `partner_longitude` | Float | GPS boylamı |
| `formen_ids` | Many2many → `res.users` | Atanmış formenler |
| `aktif` | Boolean | Aktif/Pasif |

---

### 2.3 Cari Kart Extend (`res.partner`)
Nakliye modülüne özgü alanlar standart cari kartına eklenir.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `nakliye_araci` | Boolean | İşaretlenince araç alanları görünür |
| `plaka` | Char | Araç plakası |
| `kapasite_ton` | Float | Trafik izin kapasitesi |
| `yuk_haddi_ton` | Float | Kantar fişi aşım kontrolü için |
| `sofor_gecmisi_ids` | One2many → `nakliye.arac.sofor` | Şoför geçmişi |
| `aktif_sofor` | Char (computed) | Aktif şoför adı |
| `taseron_isci_firmasi` | Boolean | İşaretlenince işçi listesi görünür |
| `isci_listesi_ids` | One2many → `nakliye.taseron.isci` | Taşeron işçi listesi |

**Alt Model: Araç Şoför Geçmişi (`nakliye.arac.sofor`)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `arac_id` | Many2one → `res.partner` | Bağlı araç |
| `sofor_adi` | Char | Şoför adı (taşeron personeli) |
| `baslangic_tarihi` | Date | Göreve başlama |
| `bitis_tarihi` | Date | Görev bitiş |
| `aktif` | Boolean | Aktif şoför |

**Alt Model: Taşeron İşçi (`nakliye.taseron.isci`)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `firma_id` | Many2one → `res.partner` | Taşeron firma |
| `isci_adi` | Char | İşçi adı (elle yazılır) |
| `baslangic_tarihi` | Date | İşe başlama |
| `bitis_tarihi` | Date | İşten ayrılma |
| `aktif` | Boolean | Aktif işçi |

> **Not:** Birden fazla işçi aynı anda aktif olabilir.

---

### 2.4 Nakliyeci-Şantiye Sözleşmesi (`nakliye.sozlesme`)
Araç-şantiye bazlı km birim fiyatlarını tutar. Hakediş hesabının dayanağı.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `nakliyeci_id` | Many2one → `res.partner` | Nakliyeci firma |
| `arac_id` | Many2one → `res.partner` | Araç (nakliyecinin alt carisi) |
| `santiye_id` | Many2one → `nakliye.santiye` | Şantiye |
| `baslangic_tarihi` | Date | Sözleşme başlangıcı |
| `bitis_tarihi` | Date | Sözleşme bitişi |
| `aktif` | Boolean | Aktif sözleşme |
| `satir_ids` | One2many → `nakliye.sozlesme.satir` | Lokasyon bazlı fiyatlar |

**İş Kuralı:** Aynı araç + şantiye kombinasyonu için aynı anda yalnızca bir aktif sözleşme olabilir. Fiyat değişince eski sözleşme pasife alınır, yeni oluşturulur.

**Alt Model: Sözleşme Fiyat Satırı (`nakliye.sozlesme.satir`)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `sozlesme_id` | Many2one → `nakliye.sozlesme` | Ana sözleşme |
| `lokasyon_tipi` | Selection | Moloz/Döküm/Mıcır/Kum/Stabilize |
| `lokasyon_id` | Many2one → `res.partner` | Lokasyon |
| `km_birim_fiyat_dolu` | Float | Dolu sefer TL/km |
| `km_birim_fiyat_bos` | Float | Boş sefer TL/km |

---

### 2.5 Çalışan Extend (`hr.employee`)
Firma personeli için çalışma tipi ve şantiye atama geçmişi.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `calisma_tipi` | Selection | İşçi/Personel/Formen/Yönetici Formen/Şantiye Şefi/Şantiye Muhasebecisi/Muhasebe Müdürü |
| `odoo_user_id` | Many2one → `res.users` | Odoo kullanıcı bağlantısı |
| `santiye_atama_ids` | One2many → `nakliye.employee.santiye` | Şantiye atamaları |
| `aktif_santiye_id` | Many2one (computed) | Aktif şantiye |

**Alt Model: Çalışan Şantiye Ataması (`nakliye.employee.santiye`)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `employee_id` | Many2one → `hr.employee` | Çalışan |
| `santiye_id` | Many2one → `nakliye.santiye` | Şantiye |
| `baslangic_tarihi` | Date | Atama başlangıcı |
| `bitis_tarihi` | Date | Atama bitişi |
| `gecis_nedeni` | Selection | İlk Atama/Şantiye Değişikliği/Geçici Görev/İşten Ayrılma |
| `aktif` | Boolean | Aktif atama |
| `tanimlayan_id` | Many2one → `res.users` | Kaydı oluşturan (otomatik) |

**İş Kuralı:** Bir çalışanın aynı anda yalnızca bir aktif şantiye ataması olabilir.

---

### 2.6 Günlük Plan (`nakliye.gunluk.plan`)
Formenin her sabah oluşturduğu günlük araç çalışma planı.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `tarih` | Date | Plan tarihi (bugün) |
| `santiye_id` | Many2one → `nakliye.santiye` | Şantiye |
| `saha_id` | Many2one → `nakliye.saha` | Saha (şantiyeye göre filtrelenir) |
| `formen_id` | Many2one → `res.users` | Formen (giriş yapan kullanıcı) |
| `durum` | Selection | Taslak/Onaylandı/Kapalı |
| `satir_ids` | One2many → `nakliye.plan.satir` | Plan satırları |

**Alt Model: Plan Satırı (`nakliye.plan.satir`)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `plan_id` | Many2one → `nakliye.gunluk.plan` | Ana plan |
| `arac_id` | Many2one → `res.partner` | Araç |
| `sofor_id` | Many2one → `res.partner` | Şoför |
| `gorev_tipi` | Selection | Moloz/Döküm/Mıcır/Kum/Stabilize |
| `kazi_yeri` | Char | Kazı yeri |
| `dokum_yeri_id` | Many2one → `res.partner` | Döküm yeri |
| `tedarikci_id` | Many2one → `res.partner` | Tedarikçi |
| `plan_km_gidis` | Float | Planlanan gidiş km |
| `plan_km_donus` | Float | Planlanan dönüş km |
| `sefer_tipi` | Selection | Dolu-Boş/Boş-Dolu/Dolu-Dolu |

---

### 2.7 Döküm Fişi (`nakliye.dokum.fisi`)
Moloz/döküm seferlerinin km takibi.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `plan_satir_id` | Many2one → `nakliye.plan.satir` | Plan satırı |
| `santiye_id` | Many2one (related) | Şantiye (otomatik) |
| `saha_id` | Many2one (related) | Saha (otomatik) |
| `arac_id` | Many2one (related) | Araç (otomatik) |
| `tarih` | Date (related) | Tarih (otomatik) |
| `gidis_km` | Float | Gidiş km (formen girer) |
| `donus_km` | Float | Dönüş km (formen girer) |
| `toplam_km` | Float (computed) | Gidiş + Dönüş |
| `dokum_yeri_id` | Many2one → `res.partner` | Fiili döküm yeri |
| `durum` | Selection | Taslak/Onaylandı/İptal |

**İş Kuralları:**
- Km negatif olamaz
- Toplam km 0 iken onaylanamaz
- İptal edilen fiş hakediş hesabına dahil edilmez

---

### 2.8 Kantar Fişi (`nakliye.kantar.fisi`)
Kum/mıcır/stabilize malzeme tartım kayıtları.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `plan_satir_id` | Many2one → `nakliye.plan.satir` | Plan satırı |
| `santiye_id` | Many2one (related) | Şantiye (otomatik) |
| `saha_id` | Many2one (related) | Saha (otomatik) |
| `arac_id` | Many2one (related) | Araç (otomatik) |
| `tarih` | Date (related) | Tarih (otomatik) |
| `tedarikci_id` | Many2one → `res.partner` | Tedarikçi |
| `fis_no` | Char | Orijinal kantar fiş numarası |
| `tara_kg` | Float | Boş araç ağırlığı |
| `brut_kg` | Float | Dolu araç ağırlığı |
| `net_kg` | Float (computed) | Brüt - Tara |
| `net_ton` | Float (computed) | Net kg / 1000 |
| `tonaj_asimi` | Boolean (computed) | Yük haddi aşıldı mı |
| `asim_miktari_ton` | Float (computed) | Aşım miktarı |
| `durum` | Selection | Taslak/Onaylandı/İptal |

**İş Kuralı — Tonaj Aşımı:**
- `net_ton > arac.yuk_haddi_ton` → `tonaj_asimi = True`
- Tonaj aşımında nakliyeci trafik cezasından sorumludur
- Hakediş hesabında aşım tutarı nakliyeciye yansıtılır

---

### 2.9 Yakıt Fişi (`nakliye.yakit.fisi`)
Araç yakıt alım kayıtları. Şantiye bazlı takip.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `plan_satir_id` | Many2one → `nakliye.plan.satir` | Plan satırı |
| `santiye_id` | Many2one (related) | Şantiye (otomatik) |
| `arac_id` | Many2one (related) | Araç (otomatik) |
| `tarih` | Date (related) | Tarih (otomatik) |
| `istasyon_id` | Many2one → `res.partner` | Akaryakıt istasyonu |
| `fis_no` | Char | Fiş numarası |
| `litre` | Float | Yakıt miktarı |
| `birim_fiyat` | Float | TL/litre |
| `toplam_tutar` | Float (computed) | Litre × Birim Fiyat |
| `durum` | Selection | Taslak/Onaylandı/İptal |

---

### 2.10 Yemek Planı (`nakliye.yemek.plan`)
Şantiye bazlı günlük yemek dağıtım planı. Versiyonlanır.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `name` | Char | Plan adı |
| `santiye_id` | Many2one → `nakliye.santiye` | Şantiye |
| `baslangic_tarihi` | Date | Plan geçerlilik başlangıcı |
| `bitis_tarihi` | Date | Plan geçerlilik bitişi |
| `aktif` | Boolean | Aktif plan |
| `satir_ids` | One2many → `nakliye.yemek.plan.satir` | Plan satırları |

**İş Kuralı:** Bir şantiyede aynı anda yalnızca bir aktif plan olabilir.

**Versiyonlama:** "Planı Güncelle (Dublike Et)" butonu mevcut planı pasife alır, aynı satırlarla yeni plan oluşturur.

**Alt Model: Yemek Planı Satırı (`nakliye.yemek.plan.satir`)**

4 tip satır:

| Tip | Kaynak | Açıklama |
|-----|--------|----------|
| `firma_isci` | `hr.employee` (calisma_tipi=isci) | Firma işçisi |
| `personel` | `hr.employee` (formen/şef/muhasebeci) | Firma personeli |
| `taseron_nakliye` | Nakliye firması → Araç → Aktif Şoför | Taşeron şoförü |
| `taseron_isci` | Taşeron firma → İşçi listesi | Taşeron işçisi |

---

### 2.11 Yemek Puantajı (`nakliye.yemek.puantaj`)
Günlük yemek dağıtım takibi. Plandan otomatik kopyalanır.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `tarih` | Date | Puantaj tarihi |
| `santiye_id` | Many2one → `nakliye.santiye` | Şantiye |
| `plan_id` | Many2one → `nakliye.yemek.plan` | Aktif plan (otomatik gelir) |
| `yemek_firmasi_id` | Many2one → `res.partner` | Yemek firması |
| `satir_ids` | One2many → `nakliye.yemek.puantaj.satir` | Puantaj satırları |
| `toplam_personel` | Integer (computed) | Toplam personel |
| `toplam_taseron_sofor` | Integer (computed) | Toplam taşeron şoför |
| `toplam_taseron_isci` | Integer (computed) | Toplam taşeron işçi |
| `toplam_yemek` | Integer (computed) | Toplam yemek |
| `toplam_tutar` | Float (computed) | Toplam tutar |
| `durum` | Selection | Taslak/Onaylandı/İptal |

**İş Akışı:** Plan seçilince `@api.onchange` ile satırlar otomatik kopyalanır. Formen sadece adet değiştirir (fazla gelmeyen 0 yapılır).

---

### 2.12 Hakediş (`nakliye.hakedis`)
Nakliyeci ödeme hesabı. Wizard tarafından oluşturulur.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `donem_baslangic` | Date | Hakediş dönemi başlangıcı |
| `donem_bitis` | Date | Hakediş dönemi bitişi |
| `nakliyeci_id` | Many2one → `res.partner` | Nakliyeci |
| `arac_id` | Many2one → `res.partner` | Araç |
| `santiye_id` | Many2one → `nakliye.santiye` | Şantiye |
| `satir_ids` | One2many → `nakliye.hakedis.satir` | Hakediş satırları |
| `tevkifat_orani` | Float | Uygulanan tevkifat oranı |
| `toplam_km` | Float (computed) | Toplam km |
| `brut_tutar` | Float (computed) | Brüt hakediş tutarı |
| `tevkifat_tutari` | Float (computed) | Tevkifat tutarı |
| `net_tutar` | Float (computed) | Net ödeme tutarı |
| `durum` | Selection | Taslak/Onay Bekliyor/Onaylandı/Ödendi/İptal |

**Alt Model: Hakediş Satırı (`nakliye.hakedis.satir`)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `hakedis_id` | Many2one → `nakliye.hakedis` | Ana hakediş |
| `satir_tipi` | Selection | Moloz/Döküm/Mıcır/Kum/Stabilize |
| `dokum_fisi_id` | Many2one → `nakliye.dokum.fisi` | Bağlı fiş |
| `gidis_km` | Float | Gidiş km |
| `donus_km` | Float | Dönüş km |
| `toplam_km` | Float (computed) | Toplam km |
| `km_fiyat_dolu` | Float | Dolu sefer fiyatı (sözleşmeden) |
| `km_fiyat_bos` | Float | Boş sefer fiyatı (sözleşmeden) |
| `tutar` | Float (computed) | (Gidiş × Dolu) + (Dönüş × Boş) |

---

### 2.13 Hakediş Wizard (`nakliye.hakedis.wizard`)
`TransientModel` — geçici kayıt, işlem bitince silinir.

**Akış:**
1. Muhasebeci dönem, şantiye, nakliyeci, araç seçer
2. Sistem aktif sözleşmeyi bulur
3. Dönemdeki onaylı döküm fişlerini toplar
4. Sözleşmeden lokasyon bazlı fiyatı alır
5. Hakediş kaydı oluşturur, forma yönlendirir

---

### 2.14 Sistem Ayarları (`nakliye.ayarlar`)
`TransientModel` — sistem genelinde geçerli parametreler.

| Alan | Tip | Varsayılan | Açıklama |
|------|-----|-----------|----------|
| `tevkifat_orani` | Float | %3 | Nakliye tevkifat oranı |
| `yemek_bedeli` | Float | 0 | Günlük yemek bedeli |
| `sozlesme_uyari_gun` | Integer | 30 | Sözleşme bitiş uyarı süresi |
| `hakedis_hatirlatma_gun` | Integer | 3 | Hakediş onay hatırlatma süresi |

---

### 2.15 Zimmet Takibi (`maintenance.equipment` extend)
Odoo'nun Maintenance modülü extend edilerek zimmet alanları eklendi.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `santiye_id` | Many2one → `nakliye.santiye` | Ekipmanın şantiyesi |
| `zimmet_alan_id` | Many2one → `hr.employee` | Zimmeti alan çalışan |
| `zimmet_tarihi` | Date | Zimmet tarihi |
| `iade_tarihi` | Date | İade tarihi |
| `zimmet_durumu` | Selection | Zimmetli/İade Edildi/Kayıp |
| `zimmet_notu` | Text | Zimmet notu |

---

## 3. GÜVENLİK

### 3.1 Grup Hiyerarşisi

```
group_nakliye_admin
    └── group_nakliye_muhasebe_muduru
            └── group_nakliye_santiye_muhasebe
                    └── group_nakliye_formen
```

`implied_ids` ile her üst grup alt grubun yetkilerini miras alır.

### 3.2 Grup Yetkileri

| Grup | Tanımlamalar | Operasyon | Muhasebe | Ayarlar |
|------|-------------|-----------|----------|---------|
| Formen | Sadece okuma | Oluştur/Düzenle | Sadece okuma | — |
| Şantiye Muhasebecisi | Saha düzenle | Sadece okuma | Tam yetki (kendi şantiyesi) | — |
| Muhasebe Müdürü | Tam yetki | Sadece okuma | Tam yetki (tüm şantiyeler) | — |
| Yönetim | Sadece okuma | Sadece okuma | Sadece okuma | — |
| Admin | Tam yetki | Tam yetki | Tam yetki | Tam yetki |

### 3.3 Satır Bazlı Erişim (ir.rule)

| Model | Formen | Şantiye Muhasebecisi |
|-------|--------|---------------------|
| Saha | `saha.formen_ids` | `santiye.muhasebeci_ids` |
| Şantiye | — | `muhasebeci_ids` |
| Günlük Plan | `saha_id.formen_ids` | `santiye_id.muhasebeci_ids` |
| Döküm Fişi | `saha_id.formen_ids` | `santiye_id.muhasebeci_ids` |
| Kantar Fişi | `saha_id.formen_ids` | `santiye_id.muhasebeci_ids` |
| Yakıt Fişi | Şantiye bazlı (employee) | `santiye_id.muhasebeci_ids` |
| Hakediş | — | `santiye_id.muhasebeci_ids` |

> Muhasebe müdürü ve admin için `ir.rule` tanımlanmaz — tüm kayıtlara erişebilir.

---

## 4. ZAMANLANMIŞ GÖREVLER

### 4.1 Sözleşme Bitiş Kontrolü
- **Frekans:** Günlük
- **Model:** `nakliye.sozlesme`
- **Metod:** `action_bitis_kontrol()`
- **Mantık:** Ayarlardan `sozlesme_uyari_gun` okur, yaklaşan sözleşmelere chatter uyarısı düşürür

### 4.2 Hakediş Onay Hatırlatması
- **Frekans:** Günlük
- **Model:** `nakliye.hakedis`
- **Metod:** `action_hakedis_hatirlatma()`
- **Mantık:** Ayarlardan `hakedis_hatirlatma_gun` okur, bekleyen hakedişlere chatter uyarısı düşürür

---

## 5. RAPORLAR

### 5.1 Hakediş Raporu (QWeb PDF)
- **Model:** `nakliye.hakedis`
- **İçerik:** Nakliyeci bilgileri, dönem, araç, hakediş satırları, özet tutarlar, tevkifat
- **Erişim:** Hakediş formundan "Yazdır" butonu

---

## 6. İŞ KURALLARI ÖZETİ

1. **Şantiye İzolasyonu:** Formen sadece kendi sahalarını, şantiye muhasebecisi sadece kendi şantiyesini görür
2. **Aktif Sözleşme Tekliği:** Aynı araç + şantiye için tek aktif sözleşme
3. **Aktif Plan Tekliği:** Bir şantiyede tek aktif yemek planı
4. **Aktif Atama Tekliği:** Bir çalışanın tek aktif şantiye ataması
5. **Tonaj Aşımı:** Kantar fişinde araç yük haddini aşan yük → nakliyeci sorumlu
6. **Tevkifat:** Fiscal position üzerinden yönetilir, ayarlardan oran belirlenir
7. **Geçmiş Koruma:** Fiyat değişikliğinde eski sözleşme pasife alınır, geçmiş hakedişler korunur
8. **Km Validasyonu:** Negatif km, 0 km onayı engellenmiştir

---

## 7. DOMAIN FİLTRELERİ

| Form | Alan | Domain |
|------|------|--------|
| Günlük Plan | `saha_id` | `[('santiye_id', '=', santiye_id)]` |
| Sözleşme | `arac_id` | `[('parent_id', '=', nakliyeci_id)]` |
| Hakediş | `arac_id` | `[('parent_id', '=', nakliyeci_id)]` |
| Yemek Plan Satırı | `arac_id` | `[('parent_id', '=', nakliye_firma_id), ('nakliye_araci', '=', True)]` |
| Yemek Plan Satırı | `taseron_isci_id` | `[('firma_id', '=', taseron_firma_id), ('aktif', '=', True)]` |
| Yemek Puantaj | `plan_id` | `[('santiye_id', '=', santiye_id), ('aktif', '=', True)]` |

---

## 8. MENÜ YAPISI

```
Nakliye Yönetim
├── Tanımlamalar
│   ├── Şantiyeler          (Muhasebe Müdürü)
│   ├── Sahalar             (Formen+)
│   ├── Sözleşmeler         (Muhasebe Müdürü)
│   └── Yemek Planları      (Şantiye Muhasebecisi+)
├── Operasyon
│   ├── Günlük Planlar      (Formen+)
│   ├── Döküm Fişleri       (Formen+)
│   ├── Kantar Fişleri      (Formen+)
│   ├── Yakıt Fişleri       (Formen+)
│   └── Yemek Puantajları   (Formen+)
├── Muhasebe
│   ├── Hakediş Oluştur     (Şantiye Muhasebecisi+)
│   └── Hakedişler          (Şantiye Muhasebecisi+)
└── Ayarlar                 (Admin)
```

---

## 9. BAĞIMLI ODOO MODÜLLERİ

| Modül | Kullanım |
|-------|---------|
| `base` | `res.partner`, `res.users` |
| `mail` | Chatter, tracking, bildirimler |
| `account` | Fiscal position (tevkifat) |
| `hr` | `hr.employee` extend |
| `fleet` | Araç referansı (bağımlılık) |
| `maintenance` | `maintenance.equipment` extend (zimmet) |

---

## 10. GELECEK GELİŞTİRMELER (TODO)

- [ ] `formen_ids` alanı `res.users` yerine `hr.employee`'ye geçirilecek
- [ ] Saha domain'leri gruplar tanımlandıktan sonra kısıtlanacak
- [ ] Tonaj aşımı hakediş kesintisi otomatikleştirilecek
- [ ] Koordinat bazlı otomatik km hesabı (Google Maps API)
- [ ] Çoklu dil desteği (i18n)
- [ ] Branch/Şube bazlı raporlama

