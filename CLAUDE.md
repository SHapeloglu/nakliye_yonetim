# CLAUDE.md — Nakliye Yönetim (Odoo 18)

Şantiye bazlı nakliye operasyonları için özel Odoo 18 modülü: şantiye/saha tanımları, nakliyeci sözleşmeleri, günlük plan, döküm/kantar/yakıt fişleri, yemek planı ve puantajı, taşeron **hakediş** hesaplama + PDF, satır bazlı yetkilendirme (formen / şantiye muhasebecisi). Standart modüller (`res.partner`, `hr.employee`, `maintenance.equipment`) genişletilerek yazıldı.

- GitHub: https://github.com/SHapeloglu/nakliye_yonetim — **PUBLIC repo**
- Sunucu: bu klasör (`/opt/odoo/custom_addons/nakliye_yonetim`) doğrudan git klonu; `odoo18-prod` (8076) ve `odoo18-test` (8074) servislerinin `addons_path`'inde.
- Odoo 17 sürümü: ayrı repo `SHapeloglu/nakliye_yonetim_17v` (06-25'ten beri durağan).
- **Tek doğruluk kaynağı: `nakliye_yonetim_spec.md`** · Mimari: `architect.md` · Görevler: `task.md` · Fikirler: `backlog.md` · Günlük: `session.md`

## Komutlar

```bash
# Önce test veritabanında güncelle
sudo -u odoo /opt/odoo/venv18/bin/python3 /opt/odoo/odoo18/odoo-bin -c /etc/odoo/odoo18-test.conf -d odoo18-test -u nakliye_yonetim --stop-after-init
sudo systemctl restart odoo18-test
# Prod (olap_prod) için aynı komut odoo18-prod.conf ile — kullanıcı onayı olmadan çalıştırma
```

## Kurallar

- Model / alan / iş kuralı değişikliğinde **önce `nakliye_yonetim_spec.md`**, sonra kod.
- Odoo 18 sözdizimi: liste görünümü `<list>` (Odoo 17'deki `<tree>` değil), `attrs` yok — `invisible="..."`/`readonly="..."` ifadeleri; aksiyonlarda `path` alanı kullanılıyor.
- Yeni model = `security/ir.model.access.csv` + gerekiyorsa `security/ir_rule.xml` kuralı (formen: `saha_id.formen_ids`, muhasebeci: `santiye_id.muhasebeci_ids`).
- Görünüm/model değişikliği sonrası modül güncellemesi (`-u nakliye_yonetim`) gerekir; sadece Python değişikliği için servis yeniden başlatma yeterli.
- **Public repo:** müşteri adı, şantiye/kişi verisi, sunucu bilgisi commit etme.
- `.gitignore` bozuk (`/__pycache____pycache__/` tek satır) — `__pycache__` için düzelt; `git add -A` öncesi `git status`'a bak.
- Oturum sonunda `session.md`'ye kayıt düş, `task.md`'yi güncelle.
