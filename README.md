# Ekipman Zimmet Takip Modülü (`equipment_custody`)

Odoo 18 üzerinde geliştirilmiş; kurumsal laboratuvar, test ve mühendislik ekipmanlarının tahsis, takip, onay, iade ve kondisyon süreçlerini uçtan uca yöneten demirbaş zimmet modülü.

---

## 1. Problem Tanımı ve Çözüm

### Excel Tabanlı Takip Problemleri
* **Mükerrer Tahsis (Çift Rezervasyon):** Aynı osiloskop veya test bilgisayarının aynı tarih aralığında birden fazla mühendise söz verilmesi.
* **Kayıp ve Sahipsiz Demirbaşlar:** Cihazın en son kimde olduğunun, ne zaman teslim alındığının bilinememesi.
* **Hasarlı İade Sorumsuzluğu:** İade edilen cihazdaki fiziksel hasarın veya kalibrasyon kaybının kime ait olduğunun tespit edilememesi.
* **Gecikme Takipsizliği:** Planlanan iade süresi geçmiş cihazların takip edilememesi.
* **Yetki Karmaşası:** Herkesin ortak listeyi serbestçe değiştirebilmesi ve geriye dönük denetim izinin (audit trail) olmaması.

### Modülün Getirdiği Çözümler
* **Çift Katmanlı Çakışma Denetimi:** `@api.onchange` ile form aşamasında anlık uyarı, `@api.constrains` ile veritabanı seviyesinde kesin mükerrer kayıt engeli.
* **Tam Sorumluluk Zinciri & Akıllı Durum Yönetimi:** Onaylanan ve teslim edilen cihazın durumu otomatik olarak `Zimmette`ye geçer, zimmetli kişi kartta güncellenir.
* **Kondisyon Kontrolü & Arıza Döngüsü (Wizard):** İade sırasında açılan sihirbazla hasarlı bildirilen cihazlar otomatik olarak `Bakımda / Arızalı` durumuna alınır; servis bitiminde tek tıkla yeniden `Müsait` yapılır.
* **Görsel Takvim & Dinamik Sayaçlar:** Ekipman tahsisleri renkli takvim (calendar) üzerinde izlenir; ekipman kartlarındaki Smart Button'lar ile geçmiş talepler filtrelenir.
* **Resmi Zimmet Tutanağı:** QWeb raporlama motoruyla tek tıkla indirilebilir teslim-tesellüm PDF çıktısı.
* **Denetim İzi (Chatter):** `mail.thread` entegrasyonuyla her durum değişikliği ve kondisyon uyarısı kalıcı olarak loglanır.

---

## 2. Mimari ve Veri Modelleri

1. **`custody.equipment` (Ekipman Tanımı):**
   * **Alanlar:** `name`, `serial_number`, `category` (Osiloskop, Laptop/PC, Ölçüm Cihazı, Diğer), `status` (Müsait, Rezerve, Zimmette, Bakımda), `current_assignee_id`, `request_ids`, `request_count`.
   * **İş Kuralları:** Durum ve mevcut zimmetli alanları aktif talepler üzerinden dinamik hesaplanır (`@api.depends`).
2. **`custody.request` (Zimmet Talebi):**
   * **Durum Makinesi:** `Taslak (draft)` -> `Onay Bekliyor (to_approve)` -> `Onaylandı (approved)` -> `Teslim Edildi (delivered)` -> `İade Alındı (returned)` / `Reddedildi (rejected)`.
   * **Doğrulama:** Çakışan tarih aralıkları tespit edilerek onay ve teslim engellenir.
3. **`custody.return.wizard` (İade ve Durum Sihirbazı):**
   * İade anında cihazın eksiksiz, hasarlı veya kalibrasyon gereksinimli olduğunu sorgulayan TransientModel.

---

## 3. Güvenlik ve Yetkilendirme (RBAC & Record Rules)

| Rol | Erişim Düzeyi | Kayıt Kuralı (Record Rule) |
|---|---|---|
| **Mühendis (Kullanıcı)** | Ekipmanları sadece okur; yeni talep oluşturur | Sadece kendi oluşturduğu talepleri görür/düzenler (`employee_id.user_id = user.id`) |
| **Yönetici** | Tüm ekipman ve talepler üzerinde tam yetki | Şirketteki tüm talepleri görür, onaylar, teslim eder, iade alır ve bakımı tamamlar |

---

## 4. Kurulum

1. `equipment_custody` klasörünü Odoo'nun `custom_addons` dizinine yerleştirin.
2. `base`, `mail` ve `hr` modüllerinin kurulu olduğundan emin olun.
3. Geliştirici Modunu açıp **Apps -> Update Apps List** deyin.
4. `equipment_custody` modülünü aratıp **Activate / Upgrade** butonuna basın.

---

## 5. Demo Verisi ile Doğrulama Senaryosu

Modül kurulumuyla birlikte 3 demo ekipman otomatik yüklenir:
* `Rigol DS1054Z Dijital Osiloskop`
* `Dell Precision 5570 Mühendislik Laptopu`
* `Fluke 87V Endüstriyel Multimetre`

### Test Adımları:
1. Mühendis olarak Rigol Osiloskop için talep açıp **Onaya Gönder**in.
2. Yönetici ile talebi **Onayla**yıp **Teslim Et** butonuna basın (Cihazın durumu sarı badge ile `Zimmette`ye döner).
3. Aynı tarihe ikinci talep açarak anlık form uyarısını ve çakışma engelini test edin.
4. Dişli menüsünden **Zimmet Teslim Tutanağı** PDF raporunu indirin.
5. **İade Al** diyerek sihirbazda *Hasarlı* seçin (Cihaz kırmızı `Bakımda`ya geçer).
6. Ekipman kartından **Bakımı Tamamla** butonuna basarak cihazı tekrar yeşil `Müsait` yapın.