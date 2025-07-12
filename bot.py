import time
import random
import os
import requests
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class SimpleInstagramBot:
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.deepseek_api_key = config.get('deepseek_api_key', None)
        self.driver = None
        
    def setup_chrome_driver(self):
        """Chrome driver kurulumu - Render için basit"""
        print("🔧 Chrome başlatılıyor...")
        
        from selenium.webdriver.chrome.service import Service
        
        options = webdriver.ChromeOptions()
        
        # Render için gerekli ayarlar
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--single-process')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        
        # Chrome binary (Aptfile ile kurulacak)
        chrome_paths = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/opt/google/chrome/google-chrome'  # Alternatif yol
        ]
        
        chrome_found = False
        for path in chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                chrome_found = True
                print(f"✅ Chrome bulundu: {path}")
                break
        
        if not chrome_found:
            print("⚠️ Chrome bulunamadı, chromium deneniyor...")
            # Chromium alternatifi
            options.add_argument('--disable-features=VizDisplayCompositor')
            # Chrome binary belirtme, sistem defaultunu kullan
        
        # ChromeDriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except:
            # Fallback
            service = Service('/usr/local/bin/chromedriver')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1366, 768)
        
        print("✅ Chrome hazır!")
    
    def test_instagram(self):
        """Instagram'a basit bağlantı testi"""
        try:
            print("🔗 Instagram'a bağlanılıyor...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Sayfa yüklendi mi?
            title = self.driver.title
            print(f"📄 Sayfa başlığı: {title}")
            
            if "Instagram" in title:
                print("✅ Instagram sayfası yüklendi!")
                return True
            else:
                print("❌ Instagram sayfası yüklenemedi!")
                return False
                
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return False
    
    def run(self):
        """Ana test döngüsü"""
        print("🚀 RENDER CHROME TEST BAŞLATIYOR...")
        print("="*50)
        
        try:
            # Chrome başlat
            self.setup_chrome_driver()
            
            # Instagram testi
            if self.test_instagram():
                print("🎉 TEST BAŞARILI!")
                print("✅ Chrome çalışıyor")
                print("✅ Instagram'a erişim var")
                print("✅ Render deployment başarılı")
            else:
                print("❌ TEST BAŞARISIZ!")
            
            # 60 saniye bekle
            print("⏰ 60 saniye test süresi...")
            for i in range(60):
                print(f"⏱️  {60-i} saniye kaldı...")
                time.sleep(1)
            
            print("✅ Test tamamlandı!")
            
        except Exception as e:
            print(f"❌ Test hatası: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("👋 Chrome kapatıldı!")
                except:
                    pass
            print("🏁 Test sonlandırıldı!")

# Ana çalıştırma
if __name__ == "__main__":
    config = {
        'username': os.environ.get('INSTAGRAM_USERNAME', 'test_user'),
        'password': os.environ.get('INSTAGRAM_PASSWORD', 'test_pass'),
        'deepseek_api_key': os.environ.get('DEEPSEEK_API_KEY', None)
    }
    
    print("🚀 RENDER CHROME + INSTAGRAM TEST")
    print("🎯 Sadece bağlantı testi yapılıyor")
    print("="*50)
    
    bot = SimpleInstagramBot(config)
    bot.run()
