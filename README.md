# Nakliye Yönetim — Odoo 18 Modülü

Şantiye bazlı nakliye operasyonlarını (araç sefer takibi, kantar/döküm/yakıt
fişleri, yemek planlaması, taşeron hakediş hesaplama) uçtan uca yöneten
özel Odoo modülü.

> 📄 **Detaylı teknik spesifikasyon için:** [`nakliye_yonetim_spec.md`](./nakliye_yonetim_spec.md)
> Bu dosya tüm veri modellerini, alanlarını, iş kurallarını, güvenlik
> yapısını ve menü hiyerarşisini eksiksiz açıklıyor — bu README sadece
> hızlı bir giriş kapısı.

---

## Bu Modül Ne İşe Yarar?

Nakliye/inşaat şantiyelerinde günlük olarak:
- Araçların hangi şantiye/sahada, hangi görevle (moloz, döküm, mıcır, kum,
  stabilize) çalışacağının **planlanması**,
- Fiili seferlerin (döküm km'si, kantar tartımı, yakıt alımı) **kayıt
  altına alınması**,
- Şantiye personeli ve taşeron işçilerinin **yemek dağıtımının takibi**,
- Nakliyeci firmalara **sözleşme bazlı hakediş** hesaplanması ve PDF rapor
  üretilmesi

gibi operasyonel süreçleri Odoo içinde standart modülleri (`res.partner`,
`hr.employee`, `maintenance.equipment`) genişleterek yönetir — ayrı bir
sistem kurmak yerine mevcut Odoo altyapısına entegre olur.

## Mimari Yaklaşım

- Sıfırdan model yazmak yerine **mevcut Odoo modülleri extend edilir**
  (`res.partner` → araç/nakliyeci, `hr.employee` → personel, vb.)
- Şantiye bazlı veri izolasyonu `ir.rule` ile sağlanır — bir formen sadece
  kendi sahasını, bir şantiye muhasebecisi sadece kendi şantiyesini görür
- Hiyerarşik yetki grupları: `Formen → Şantiye Muhasebecisi → Muhasebe
  Müdürü → Admin`

Tam model listesi, alan tablosu ve iş kuralları için spec dosyasındaki
**Bölüm 2 (Veri Modelleri)** ve **Bölüm 6 (İş Kuralları Özeti)**'ne bakın.

## Kurulum

Bu bir Odoo **addon** modülüdür, bağımsız çalışan bir uygulama değildir.

1. Modül klasörünü Odoo'nun `addons_path`'inde tanımlı bir dizine kopyalayın
   (bu sunucuda: `/opt/odoo/custom_addons/nakliye_yonetim`)
2. Odoo servisini yeniden başlatın:
   ```bash
   sudo systemctl restart odoo18   # veya sunucudaki servis adı neyse
   ```
3. Odoo arayüzünde **Ayarlar → Geliştirici Modu**'nu açın (gerekliyse)
4. **Uygulamalar** menüsünden "Nakliye Yönetim" araması yapıp **Kur**'a
   tıklayın

### Bağımlılıklar

Bu modül şu standart Odoo modüllerinin kurulu olmasını gerektirir:
`base`, `mail`, `account`, `hr`, `fleet`, `maintenance`
(Kurulum sırasında Odoo bunları otomatik olarak da kurabilir.)

## Menü Yapısı (Özet)

```
Nakliye Yönetim
├── Tanımlamalar   (Şantiyeler, Sahalar, Sözleşmeler, Yemek Planları)
├── Operasyon      (Günlük Planlar, Döküm/Kantar/Yakıt Fişleri, Yemek Puantajları)
├── Muhasebe       (Hakediş Oluştur, Hakedişler)
└── Ayarlar        (Sistem parametreleri — tevkifat oranı vb.)
```

Hangi grubun hangi menüye erişebildiğinin tam tablosu için spec
dosyasındaki **Bölüm 3 (Güvenlik)**'e bakın.

## Geliştirmeye Katkı

- Yeni bir alan/model eklerken önce `nakliye_yonetim_spec.md`'yi güncelleyin
  — bu dosya kod ile senkron tutulan tek kaynak (source of truth) olarak
  tasarlandı.
- Yeni bir view eklerken `__manifest__.py`'nin `data` listesine eklemeyi
  unutmayın, aksi halde Odoo XML'i yüklemez.
- Güvenlik kuralı (`ir_rule.xml`) eklerken mevcut grup hiyerarşisine
  (`implied_ids`) dikkat edin — üst grup zaten alt grubun yetkilerini
  miras alıyor, tekrar tanımlamaya gerek yok.

**Bilinen eksikler / planlanan geliştirmeler** için spec dosyasındaki
**Bölüm 10 (Gelecek Geliştirmeler)** listesine bakın — örneğin
`formen_ids` alanının `res.users`'tan `hr.employee`'ye taşınması ve
koordinat bazlı otomatik km hesabı (Google Maps API) gibi maddeler orada.

