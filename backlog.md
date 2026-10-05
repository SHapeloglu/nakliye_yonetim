# backlog.md — Nakliye Yönetim — Odoo 18 Modülü Fikir / Özellik Havuzu

Bu dosya henüz önceliklendirilmemiş, "bir gün yapılabilir" fikirler ve özellik talepleri içindir. Bir fikir somutlaşıp sıraya girdiğinde buradan çıkar, `task.md`ye taşınır.

## Fikirler

_(henüz boş — yeni bir fikir geldiğinde aşağıdaki şablonla ekle)_

## Koddaki TODO / FIXME Notları

- `models/gunluk_plan.py:33` — TODO: Faz 3: hr.employee [calisma_tipi=formen] ile kısıtlanacak
- `models/gunluk_plan.py:82` — TODO: Faz 3: domain — sadece aktif nakliyecilerin araçları
- `models/gunluk_plan.py:111` — TODO: Faz 3: domain — döküm yeri tipindeki lokasyonlar
- `models/gunluk_plan.py:116` — TODO: Faz 3: domain — tedarikçi tipindeki lokasyonlar
- `models/saha.py:23` — TODO: Faz 3: domain gruplar tanımlandıktan sonra
- `models/santiye.py:14` — TODO: Faz 3: domain — group_nakliye_santiye_muhasebe ile kısıtlanacak
- `models/sozlesme.py:105` — TODO: Faz 3: lokasyon tipine göre filtrelenecek

## Ekleme Şablonu

```markdown
### Başlık

- **Kategori:** yeni özellik / iyileştirme / teknik borç / araştırma
- **Neden istendi:** kısa gerekçe
- **Notlar:** büyüklük tahmini, bağımlılıklar, riskler
```
