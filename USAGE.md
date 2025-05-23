# ZEKA Kullanım Kılavuzu

Bu belge, ZEKA (Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı) uygulamasının nasıl kullanılacağını detaylı bir şekilde açıklamaktadır.

## İçindekiler

1. [Başlangıç](#başlangıç)
2. [Temel Kullanım](#temel-kullanım)
3. [Dil ve İletişim Tarzı Ayarları](#dil-ve-i̇letişim-tarzı-ayarları)
4. [Çeviri İşlemleri](#çeviri-i̇şlemleri)
5. [Bellek ve Semantik Arama](#bellek-ve-semantik-arama)
6. [OpenRouter API Kullanımı](#openrouter-api-kullanımı)
7. [Ses Komutları](#ses-komutları)
8. [Gelişmiş Özellikler](#gelişmiş-özellikler)
9. [Sorun Giderme](#sorun-giderme)

## Başlangıç

### Kurulum

ZEKA'yı kullanmaya başlamadan önce, aşağıdaki adımları izleyerek kurulumu tamamlamanız gerekmektedir:

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/kullanici/zeka.git
   cd zeka
   ```

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Çevre değişkenlerini ayarlayın:
   - `.env.example` dosyasını kopyalayıp `.env` olarak adlandırın.
   - Gerekli API anahtarlarını ve ayarları doldurun:
     ```
     OPENAI_API_KEY=your_openai_api_key
     OPENROUTER_API_KEY=your_openrouter_api_key
     ```

4. Vektör veritabanı dizinini oluşturun:
   ```bash
   mkdir -p data/vector_db
   ```

5. Uygulamayı başlatın:
   ```bash
   python src/main.py
   ```

### İlk Etkileşim

Uygulama başlatıldıktan sonra, komut satırı arayüzü veya web arayüzü (eğer etkinleştirilmişse) üzerinden ZEKA ile etkileşime geçebilirsiniz. İlk etkileşim için basit bir selamlama ile başlayabilirsiniz:

```
Kullanıcı: Merhaba, ben [Adınız]. Seninle tanışmak istiyorum.
```

ZEKA, sizinle tanışacak ve nasıl yardımcı olabileceğini soracaktır.

## Temel Kullanım

### Genel Sorular

ZEKA'ya genel bilgi soruları sorabilirsiniz:

```
Kullanıcı: Yapay zeka nedir?
```

```
Kullanıcı: Kuantum bilgisayarlar nasıl çalışır?
```

```
Kullanıcı: Türkiye'nin başkenti neresidir?
```

### Günlük Konuşmalar

Günlük konuşmalar için doğal dil kullanabilirsiniz:

```
Kullanıcı: Bugün nasılsın?
```

```
Kullanıcı: Hava durumu nasıl?
```

```
Kullanıcı: Bana bir fıkra anlat.
```

### Yardım İsteme

Herhangi bir zamanda yardım isteyebilirsiniz:

```
Kullanıcı: Bana yardım et.
```

```
Kullanıcı: Neler yapabilirsin?
```

```
Kullanıcı: Komutları göster.
```

## Dil ve İletişim Tarzı Ayarları

### Dil Değiştirme

ZEKA, çeşitli dillerde iletişim kurabilir. Dil değiştirmek için:

```
Kullanıcı: Dili İngilizce olarak ayarla.
```

```
Kullanıcı: Türkçe konuş.
```

Desteklenen diller:
- Türkçe (tr)
- İngilizce (en)
- Almanca (de)
- Fransızca (fr)
- İspanyolca (es)
- İtalyanca (it)

### İletişim Tarzı Değiştirme

ZEKA'nın iletişim tarzını değiştirebilirsiniz:

```
Kullanıcı: Resmi bir şekilde konuş.
```

```
Kullanıcı: Samimi bir tarz kullan.
```

```
Kullanıcı: Teknik bir dil kullan.
```

Desteklenen iletişim tarzları:
- Resmi (formal)
- Nötr (neutral)
- Samimi (friendly)
- Profesyonel (professional)
- Teknik (technical)
- Basit (simple)

## Çeviri İşlemleri

ZEKA, metinleri farklı diller arasında çevirebilir:

```
Kullanıcı: Bu metni İngilizce'ye çevir: Merhaba dünya, nasılsın?
```

```
Kullanıcı: Fransızca'dan Türkçe'ye çevir: Bonjour le monde, comment ça va?
```

```
Kullanıcı: "Hello, how are you today?" cümlesini Türkçe'ye çevir.
```

## Bellek ve Semantik Arama

ZEKA, önceki konuşmalarınızı hatırlayabilir ve semantik arama yapabilir:

```
Kullanıcı: Daha önce yapay zeka hakkında ne konuşmuştuk?
```

```
Kullanıcı: Geçmiş konuşmalarımızda Python ile ilgili ne vardı?
```

```
Kullanıcı: Son konuşmamızı hatırlıyor musun?
```

## OpenRouter API Kullanımı

ZEKA, OpenRouter API aracılığıyla çeşitli dil modellerine erişebilir:

```
Kullanıcı: Claude modeli ile yanıt ver: Kuantum bilgisayarlar nasıl çalışır?
```

```
Kullanıcı: Llama modeli kullanarak bir hikaye yaz.
```

```
Kullanıcı: Mistral modeli ile şiir yaz.
```

Belirli bir model kullanmak için:

```
Kullanıcı: anthropic/claude-3-opus modelini kullanarak yanıt ver: [Sorunuz]
```

```
Kullanıcı: meta/llama-3 modelini kullanarak yanıt ver: [Sorunuz]
```

## Ses Komutları

Eğer ses özellikleri etkinleştirilmişse, ZEKA'yı sesli komutlarla da kullanabilirsiniz:

1. Uyandırma kelimesini söyleyin: "Hey ZEKA"
2. Uyandırma kelimesinden sonra komutunuzu söyleyin
3. ZEKA, komutunuzu işleyecek ve sesli yanıt verecektir

Ses ayarlarını değiştirmek için:

```
Kullanıcı: Ses seviyesini artır.
```

```
Kullanıcı: Ses seviyesini azalt.
```

```
Kullanıcı: Sesi kapat.
```

## Gelişmiş Özellikler

### Metin Analizi

ZEKA, metinleri analiz edebilir:

```
Kullanıcı: Bu metni analiz et: [Metin]
```

### Metin Özetleme

ZEKA, uzun metinleri özetleyebilir:

```
Kullanıcı: Bu metni özetle: [Uzun metin]
```

### Kod Yardımı

ZEKA, kod yazma ve analiz etme konusunda yardımcı olabilir:

```
Kullanıcı: Python'da bir dosyayı nasıl okurum?
```

```
Kullanıcı: Bu kodu optimize et: [Kod]
```

```
Kullanıcı: Bu hatayı düzelt: [Hata mesajı ve kod]
```

## Sorun Giderme

### Genel Sorunlar

1. **ZEKA yanıt vermiyor**
   - Uygulamanın çalıştığından emin olun
   - `.env` dosyasındaki API anahtarlarını kontrol edin
   - Log dosyalarını kontrol edin: `logs/` dizininde

2. **API Hataları**
   - API anahtarlarınızın doğru olduğundan emin olun
   - API kotanızı kontrol edin
   - İnternet bağlantınızı kontrol edin

3. **Vektör Veritabanı Sorunları**
   - `data/vector_db` dizininin var olduğundan emin olun
   - Disk alanınızın yeterli olduğunu kontrol edin

4. **Bellek Sorunları**
   - Uygulamayı yeniden başlatın
   - Bellek önbelleğini temizleyin: `rm -rf data/vector_db/*`

### Log Dosyaları

Sorun giderme için log dosyalarını kontrol edebilirsiniz:

```bash
cat logs/zeka.log
```

```bash
cat logs/errors.log
```

### Yardım Alma

Daha fazla yardım için:

1. GitHub deposundaki sorunlar (issues) bölümünü ziyaret edin
2. Topluluk forumlarına katılın
3. Geliştirici ekibiyle iletişime geçin

---

Bu kılavuz, ZEKA'nın temel ve gelişmiş özelliklerini kapsamaktadır. Yeni özellikler eklendikçe bu belge güncellenecektir.

Son güncelleme: [Tarih]
