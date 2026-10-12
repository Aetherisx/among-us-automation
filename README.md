# Among Us: Otomasyon Asistanı

Bu proje, Python kullanılarak geliştirilmiş gerçek zamanlı bir Among Us masaüstü asistanıdır. Görüntü işleme ve hafıza tamponu teknikleri kullanılarak oyunculara oyun içi analiz ve hızlı iletişim imkanı sunar.

## Temel Özellikler

*   **Zaman Makinesi (Visual Memory Buffer):** Arka planda `mss` kütüphanesi ile sürekli ekran yakalar. Son 8 saniyelik (6 frame) görüntüyü hafızada tutarak oyuncunun anlık bir olayı (kill/vent) kaçırması durumunda geriye dönük kareler arasında gezinmesini sağlar.
*   **Piksel Tabanlı Renk Dedektifi:** Dondurulmuş ekranda bir karaktere tıklandığında, tıklanan pikselin RGB değerlerini analiz eder. Kostüm ve gölge tonlarını matematiksel uzaklık hesabı ile karşılaştırarak 18 farklı Among Us rengini otomatik tespit eder.
*   **The Skeld Harita Mimarisi:** Oyunun en popüler haritası The Skeld'deki tüm odalar, bölgelere (Sol, Orta, Sağ) ayrılarak hızlı seçilebilir bir arayüzde sunulmuştur.
*   **Pano (Clipboard) Otomasyonu:** Seçilen renk, oda ve şüpheli eylemi birleştirerek İngilizce cümleler üretir ve `pyperclip` kütüphanesiyle tek tıkla panoya kopyalar. 
*   **Overlay (Üstte Kalma) Tasarımı:** `Tkinter` kullanılarak %94 saydamlık (alpha 0.94) oranına sahip ve her zaman oyun ekranının üstünde kalacak (`-topmost`) bir arayüz olarak tasarlanmıştır.

## Kullanılan Teknolojiler

*   **Dil:** Python
*   **Arayüz (GUI):** Tkinter
*   **Görüntü İşleme & Ekran Yakalama:** `mss`, `Pillow (PIL)`
*   **Sistem Entegrasyonu:** `pyperclip` (Pano yönetimi), `ctypes` (Windows DPI ölçeklendirme optimizasyonu)
*   **Asenkron Yapı:** `threading` (Ekran yakalama işleminin ana arayüzü dondurmaması için)

## Nasıl Çalışır?
1. Uygulama başlatıldığında arka planda bir thread (iş parçacığı) sürekli oyun ekranını analiz eder.
2. Şüpheli bir durum görüldüğünde "Dondur" butonuna basılır ve son 8 saniyelik kareler arasında ileri/geri gidilir.
3. Ekranda şüphelinin üzerine tıklanarak renk otomatik tespit edilir ve arayüzdeki haritadan bulunulan oda seçilir.
4. Hazır aksiyon butonlarından birine tıklanarak üretilen analiz cümlesi panoya kopyalanır ve oyuna yapıştırılır.
