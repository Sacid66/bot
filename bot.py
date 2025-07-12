import time
import random
import os
import requests
import json
import re
import subprocess
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def install_chrome():
    """Render'da Chrome kurulumu"""
    try:
        print("🔧 Chrome kurulumu kontrol ediliyor...")
        
        # Chrome zaten kurulu mu?
        chrome_paths = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                print(f"✅ Chrome bulundu: {path}")
                return path
        
        print("📦 Chrome kurulumu başlıyor...")
        
        # Chrome kurulum komutları
        commands = [
            "apt-get update",
            "apt-get install -y wget gnupg",
            "wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -",
            "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google.list",
            "apt-get update",
            "apt-get install -y google-chrome-stable"
        ]
        
        for cmd in commands:
            print(f"⚡ Executing: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️ Warning: {cmd} failed: {result.stderr}")
        
        # Tekrar kontrol et
        for path in chrome_paths:
            if os.path.exists(path):
                print(f"✅ Chrome kuruldu: {path}")
                return path
        
        print("❌ Chrome kurulumu başarısız!")
        return None
        
    except Exception as e:
        print(f"❌ Chrome kurulum hatası: {e}")
        return None

class RenderInstagramDMBot:
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.deepseek_api_key = config.get('deepseek_api_key', None)
        self.driver = None
        self.processed_messages = {}
        self.conversation_history = {}
        self.is_logged_in = False
        
    def setup_chrome_driver(self):
        """Chrome driver kurulumu - Render için"""
        print("🔧 Chrome başlatılıyor (Render Modu)...")
        
        # Chrome kurulumunu kontrol et
        chrome_binary = install_chrome()
        if not chrome_binary:
            raise Exception("Chrome kurulumu başarısız!")
        
        from selenium.webdriver.chrome.service import Service
        
        options = webdriver.ChromeOptions()
        
        # Render için zorunlu ayarlar
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--memory-pressure-off')
        options.add_argument('--single-process')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Hız için
        options.add_argument('--disable-javascript')  # Güvenlik için (Instagram temel JS çalışır)
        
        # Chrome binary yolunu belirt
        options.binary_location = chrome_binary
        
        # Profil dizini (geçici)
        bot_profile_dir = "/tmp/instagram_bot_profile"
        os.makedirs(bot_profile_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={bot_profile_dir}")
        options.add_argument("--profile-directory=BotProfile")
        
        # Bot tespitini engelle
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Bildirimler kapalı
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2
        }
        options.add_experimental_option('prefs', prefs)
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # ChromeDriver yolu
            driver_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver'
            ]
            
            service = None
            for path in driver_paths:
                if os.path.exists(path):
                    service = Service(path)
                    break
            
            if not service:
                # Webdriver manager kullan
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except Exception as e:
            print(f"❌ Chrome başlatma hatası: {e}")
            raise Exception("Chrome driver başlatılamadı!")
        
        # Pencere boyutu
        self.driver.set_window_size(1366, 768)
        
        print("✅ Chrome hazır! (Render optimizasyonu aktif)")
    
    def login_once_safely(self):
        """TEK SEFERLİK GİRİŞ - 2FA manuel çözüm gerekli"""
        try:
            print("🔑 Instagram'a bağlanılıyor...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Zaten giriş yapılmış mı?
            if self.check_if_logged_in():
                print("✅ Profil kaydedilmiş, zaten giriş yapılmış!")
                return True
            
            print("🔑 İlk kez giriş yapılıyor...")
            print("⚠️  DİKKAT: 2FA gerekirse bot duracak!")
            print("💡 ÇÖZÜM: Önce local'de giriş yap, profili kaydet, sonra deploy et")
            
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Çerezleri kabul et
            try:
                cookie_selectors = [
                    "//button[contains(text(), 'Allow')]",
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Kabul')]"
                ]
                for selector in cookie_selectors:
                    try:
                        cookie_btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        cookie_btn.click()
                        time.sleep(1)
                        break
                    except:
                        continue
            except:
                pass
            
            # Login formu
            try:
                username_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_input = self.driver.find_element(By.NAME, "password")
                
                username_input.clear()
                time.sleep(0.5)
                username_input.send_keys(self.username)
                time.sleep(1)
                
                password_input.clear()
                time.sleep(0.5)
                password_input.send_keys(self.password)
                time.sleep(1)
                
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
                print("✅ Login formu gönderildi")
                
            except Exception as e:
                print(f"❌ Login formu hatası: {e}")
                return False
            
            # Giriş sonucu bekle
            for attempt in range(20):
                time.sleep(3)
                current_url = self.driver.current_url
                
                print(f"📍 Giriş kontrolü {attempt+1}/20: {current_url[:100]}...")
                
                # 2FA/Challenge kontrolü
                if "challenge" in current_url:
                    print("❌ 2FA/Challenge gerekiyor!")
                    print("💡 ÇÖZÜM: Local'de önce giriş yap, profil kaydet!")
                    return False
                
                # Başarılı giriş
                if self.check_if_logged_in():
                    print("🎉 Giriş başarılı! Profil kaydedildi.")
                    self.is_logged_in = True
                    return True
                
                # Hata mesajı
                try:
                    error_msgs = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'incorrect') or contains(text(), 'error') or contains(text(), 'wrong')]")
                    if error_msgs:
                        print("❌ Giriş bilgileri hatalı!")
                        return False
                except:
                    pass
            
            print("❌ Giriş zaman aşımı!")
            return False
            
        except Exception as e:
            print(f"❌ Giriş genel hatası: {e}")
            return False
    
    def check_if_logged_in(self):
        """Giriş kontrolü"""
        try:
            current_url = self.driver.current_url
            
            if "login" in current_url or "accounts/login" in current_url:
                return False
            
            # DM linki var mı?
            try:
                dm_selectors = [
                    "//a[@href='/direct/inbox/']",
                    "//a[contains(@href, '/direct/')]",
                    "//svg[@aria-label='Direct']"
                ]
                
                for selector in dm_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        return True
            except:
                pass
            
            # Profil menüsü var mı?
            try:
                profile_elements = self.driver.find_elements(By.XPATH, "//img[@alt and contains(@alt, 'profile picture')]")
                if profile_elements:
                    return True
            except:
                pass
            
            return False
            
        except:
            return False
    
    def run(self):
        """Ana bot döngüsü - SADECE TEST"""
        print("🚀 RENDER INSTAGRAM BOT TEST...")
        print("="*50)
        
        try:
            # Chrome başlat
            self.setup_chrome_driver()
            
            # Giriş dene
            if not self.login_once_safely():
                print("❌ Giriş başarısız!")
                print("💡 ÇÖZÜM:")
                print("1. Local'de bot'u çalıştır")
                print("2. Manuel giriş yap ve profili kaydet")
                print("3. Profil klasörünü Render'a yükle")
                print("4. Tekrar deploy et")
                return
            
            print("✅ BOT BAŞARILI! Render'da çalışıyor!")
            
            # Test modunda 30 saniye bekle
            for i in range(30):
                print(f"⏰ Test süresi: {30-i} saniye kaldı...")
                time.sleep(1)
            
            print("✅ Test tamamlandı!")
            
        except Exception as e:
            print(f"❌ Bot hatası: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("👋 Chrome kapatıldı!")
                except:
                    pass
            print("🏁 Bot sonlandırıldı!")

# Ana çalıştırma
if __name__ == "__main__":
    config = {
        'username': os.environ.get('INSTAGRAM_USERNAME'),
        'password': os.environ.get('INSTAGRAM_PASSWORD'),
        'deepseek_api_key': os.environ.get('DEEPSEEK_API_KEY')
    }
    
    # Gerekli kontroller
    if not config['username']:
        print("❌ INSTAGRAM_USERNAME environment variable eksik!")
        sys.exit(1)
    if not config['password']:
        print("❌ INSTAGRAM_PASSWORD environment variable eksik!")
        sys.exit(1)
    
    print(f"✅ Instagram kullanıcısı: {config['username']}")
    print(f"✅ DeepSeek API: {'Aktif' if config['deepseek_api_key'] else 'Deaktif'}")
    
    print("🚀 RENDER TEST BOT")
    print("⚠️  2FA sorunu varsa local'de önce çalıştır!")
    print("="*50)
    
    bot = RenderInstagramDMBot(config)
    bot.run()