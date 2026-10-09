# Ekipman Zimmet Takip Modülü (`equipment_custody`)

Odoo 18 üzerinde geliştirilmiş; kurumsal laboratuvar, test ve mühendislik ekipmanlarının tahsis, takip, onay, iade ve kondisyon süreçlerini uçtan uca yöneten demirbaş zimmet modülü.

Son kullanıcı adımları için [KULLANICI_KILAVUZU.md](KULLANICI_KILAVUZU.md) dosyasına bakın.

---

## 1. Problem Tanımı ve Çözüm

### Excel Tabanlı Takip Problemleri
* **Mükerrer Tahsis (Çift Rezervasyon):** Aynı osiloskop veya test bilgisayarının aynı tarih aralığında birden fazla mühendise söz verilmesi.
* **Kayıp ve Sahipsiz Demirbaşlar:** Cihazın en son kimde olduğunun, ne zaman teslim alındığının bilinememesi.
* **Hasarlı İade Sorumsuzluğu:** İade edilen cihazdaki fiziksel hasarın veya kalibrasyon kaybının kime ait olduğunun tespit edilememesi.
* **Gecikme Takipsizliği:** Planlanan iade süresi geçmiş cihazların takip edilememesi.
* **Yetki Karmaşası:** Herkesin ortak listeyi serbestçe değiştirebilmesi ve geriye dönük denetim izinin (audit trail) olmaması.

### Modülün Getirdiği Çözümler
* **Çift Katmanlı Çakışma Denetimi:** `@api.onchange` ile form doldurulurken anlık uyarı (çakışan talep numarası ve tarihleriyle birlikte), `@api.constrains` ile kayıt seviyesinde kesin engel. Kesin kontrol, talep taslak/reddedildi/iade alındı dışındaki bir duruma geçtiğinde ve tarih ya da ekipman değiştiğinde çalışır; yalnızca `Onaylandı` ve `Teslim Edildi` durumundaki talepler çakışma sayılır.
* **Tam Sorumluluk Zinciri & Akıllı Durum Yönetimi:** Talep onaylandığında cihaz `Rezerve`, teslim edildiğinde `Zimmette` durumuna geçer; zimmetli kişi ekipman kartında otomatik güncellenir.
* **Gecikme Takibi:** Planlanan iade tarihi geçmiş ve hâlâ `Teslim Edildi` durumunda olan talepler (`is_overdue`) talep listesinde kırmızı vurgulanır.
* **Kondisyon Kontrolü & Arıza Döngüsü (Wizard):** İade sırasında açılan sihirbazda cihaz *Eksiksiz ve Sağlam*, *Hasarlı / Arızalı* veya *Kalibrasyon Gerekli* olarak işaretlenir. Son iki seçenekte cihaz otomatik olarak `Bakımda` durumuna alınır; servis bitiminde **Bakımı Tamamla** ile tek tıkla yeniden `Müsait` yapılır.
* **Görsel Takvim & Dinamik Sayaçlar:** Ekipman tahsisleri renkli takvim (calendar) üzerinde izlenir; ekipman kartındaki Smart Button ile o cihazın geçmiş talepleri listelenir.
* **Resmi Zimmet Tutanağı:** QWeb raporlama motoruyla tek tıkla indirilebilir teslim-tesellüm PDF çıktısı.
* **Denetim İzi (Chatter):** `mail.thread` entegrasyonuyla alan değişiklikleri, durum geçişleri ve iade kondisyon notları kalıcı olarak loglanır.

---

## 2. Mimari ve Veri Modelleri

1. **`custody.equipment` (Ekipman Tanımı):**
   * **Alanlar:** `name`, `serial_number`, `category` (Osiloskop, Laptop/PC, Ölçüm Cihazı, Diğer), `status` (Müsait, Rezerve, Zimmette, Bakımda), `current_assignee_id`, `request_ids`, `request_count`, `note`.
   * **İş Kuralları:** `status` ve `current_assignee_id`, bağlı taleplerin durumundan `@api.depends` ile hesaplanır ve saklanır (teslim edilmiş talep varsa `Zimmette`, onaylı talep varsa `Rezerve`, yoksa `Müsait`). `Bakımda` durumu hesaplama ile değil, iade sihirbazı ile verilir ve yalnızca **Bakımı Tamamla** butonu ile kalkar.
2. **`custody.request` (Zimmet Talebi):**
   * **Alanlar:** `name` (otomatik talep no), `employee_id`, `equipment_id`, `start_date`, `end_date` (planlanan iade), `return_date` (fiili iade), `purpose`, `state`, `is_overdue`.
   * **Durum Makinesi:** `Taslak (draft)` -> `Onay Bekliyor (to_approve)` -> `Onaylandı (approved)` -> `Teslim Edildi (delivered)` -> `İade Alındı (returned)`; onay aşamasında alternatif olarak `Reddedildi (rejected)`.
   * **Doğrulama:** Çakışan tarih aralıkları `@api.onchange` ile uyarılır, `@api.constrains` ile engellenir; **Onayla** ve **Teslim Et** butonları da aynı kontrolü yeniden çalıştırır.
3. **`custody.return.wizard` (İade ve Durum Sihirbazı, TransientModel):**
   * **Alanlar:** `request_id`, `return_condition` (Eksiksiz ve Sağlam, Hasarlı / Arızalı, Kalibrasyon Gerekli), `damage_note`.
   * **Davranış:** Talebi `İade Alındı` yapar ve fiili iade tarihini yazar; kondisyon sorunluysa cihazı `Bakımda` durumuna alır ve hem talebe hem ekipmana Chatter notu düşer.

### Modeller Arası İlişkiler

| Model | Alan | İlişki | Hedef |
|---|---|---|---|
| `custody.request` | `equipment_id` | Many2one | `custody.equipment` |
| `custody.request` | `employee_id` | Many2one | `hr.employee` (talep eden mühendis) |
| `custody.equipment` | `request_ids` | One2many | `custody.request` |
| `custody.equipment` | `current_assignee_id` | Many2one (hesaplanan) | `hr.employee` |
| `custody.return.wizard` | `request_id` | Many2one | `custody.request` |

Hem ekipman hem talep modeli `mail.thread` ve `mail.activity.mixin` kalıtımı ile Chatter desteği kazanır.

---

## 3. Güvenlik ve Yetkilendirme (RBAC & Record Rules)

| Rol | Erişim Düzeyi | Kayıt Kuralı (Record Rule) |
|---|---|---|
| **Mühendis (Kullanıcı)** | Ekipmanları sadece okur; talep oluşturur ve düzenler, silemez. İade sihirbazına erişemez | Sadece talep eden çalışanın bağlı kullanıcısı kendisi olan talepleri görür (`employee_id.user_id = user.id`) |
| **Yönetici** | Tüm ekipman ve talepler üzerinde tam yetki | Şirketteki tüm talepleri görür; onaylar, reddeder, teslim eder, iade alır ve bakımı tamamlar |

Yetkiler `security/security.xml` (gruplar ve kayıt kuralları) ile `security/ir.model.access.csv` (model bazlı erişim) dosyalarında tanımlıdır.

---

## 4. Kurulum

1. `equipment_custody` klasörünü Odoo'nun `custom_addons` dizinine yerleştirin ve bu dizinin `odoo.conf` içindeki `addons_path` değerinde bulunduğundan emin olun.
2. `base`, `mail` ve `hr` modüllerinin kurulu olduğundan emin olun.
3. Geliştirici Modunu açıp **Apps -> Update Apps List** deyin.
4. `equipment_custody` modülünü aratıp **Activate / Upgrade** butonuna basın.

Kod değişikliklerinden sonra modülü komut satırından güncellemek için:

```bash
./odoo-bin -c odoo.conf -d <veritabani_adi> -u equipment_custody
```

---

## 5. Demo Verisi ile Doğrulama Senaryosu

Modül kurulumuyla birlikte 3 demo ekipman otomatik yüklenir:
* `Rigol DS1054Z Dijital Osiloskop`
* `Dell Precision 5570 Mühendislik Laptopu`
* `Fluke 87V Endüstriyel Multimetre`

### Test Adımları:
1. Mühendis olarak Rigol Osiloskop için talep açıp **Onaya Gönder**in.
2. Yönetici ile talebi **Onayla**yın (cihaz mavi `Rezerve` olur), ardından **Teslim Et** butonuna basın (cihazın durumu sarı badge ile `Zimmette`ye döner).
3. Aynı cihaz ve çakışan tarihler için ikinci bir talep açın: form üzerinde anlık uyarı penceresi çıkar; talebi onaya göndermeye veya onaylamaya çalıştığınızda kesin çakışma hatası alırsınız.
4. Dişli menüsünden **Zimmet Teslim Tutanağı** PDF raporunu indirin.
5. **İade Al** diyerek sihirbazda *Hasarlı / Arızalı* (veya *Kalibrasyon Gerekli*) seçin (cihaz kırmızı `Bakımda`ya geçer).
6. Ekipman kartından **Bakımı Tamamla** butonuna basarak cihazı tekrar yeşil `Müsait` yapın.
7. (Opsiyonel) Planlanan iade tarihi geçmiş, teslim edilmiş bir talebin talep listesinde kırmızı göründüğünü kontrol edin.