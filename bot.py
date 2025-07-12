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
from selenium.webdriver.common.action_chains import ActionChains

class CloudInstagramDMBot:
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.deepseek_api_key = config.get('deepseek_api_key', None)
        self.driver = None
        self.processed_messages = {}
        self.conversation_history = {}
        self.is_logged_in = False
        self.is_cloud = config.get('is_cloud', False)  # Bulut modu
        
    def setup_chrome_driver(self):
        """Chrome driver kurulumu - BULUT OPTİMİZE"""
        print("🔧 Chrome başlatılıyor (Bulut Modu)...")
        
        from selenium.webdriver.chrome.service import Service
        
        options = webdriver.ChromeOptions()
        
        # BULUT SUNUCU İÇİN ZORUNLU AYARLAR
        if self.is_cloud:
            print("☁️ Bulut sunucu ayarları aktif!")
            options.add_argument('--headless')  # GUI yok
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
            options.add_argument('--single-process')  # Düşük RAM kullanımı
        
        # Özel bot profili (kalıcı giriş için)
        if self.is_cloud:
            # Bulutta geçici dizin kullan
            bot_profile_dir = "/tmp/instagram_bot_profile"
        else:
            bot_profile_dir = os.path.join(os.getcwd(), "instagram_bot_profile")
            
        os.makedirs(bot_profile_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={bot_profile_dir}")
        options.add_argument("--profile-directory=BotProfile")
        
        # Temel güvenlik ayarları
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Bildirimler kapalı
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2  # Resimleri yükleme (hız için)
        }
        options.add_experimental_option('prefs', prefs)
        
        # User agent (bot tespitini engelle)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Bulut sunucuda chrome yolu farklı olabilir
            if self.is_cloud:
                # Çoğu bulut serviste chrome binary yolu
                chrome_paths = [
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/google-chrome',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium'
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        options.binary_location = path
                        break
                        
                # ChromeDriver yolu da farklı olabilir
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
            else:
                # Yerel geliştirme
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except Exception as e:
            print(f"❌ Chrome başlatma hatası: {e}")
            # Fallback: sistem chrome'u dene
            try:
                self.driver = webdriver.Chrome(options=options)
            except:
                raise Exception("Chrome driver başlatılamadı!")
        
        # Pencere boyutu (headless modda da çalışır)
        self.driver.set_window_size(1366, 768)
        
        # Bot izlerini gizle
        if not self.is_cloud:  # Headless modda çalışmaz
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
            })
        
        print("✅ Chrome hazır! (Bulut optimizasyonu aktif)" if self.is_cloud else "✅ Chrome hazır!")
    
    def login_once_safely(self):
        """Tek seferlik giriş - Bulut için optimize"""
        try:
            print("🔑 Instagram'a bağlanılıyor...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)  # Bulut sunucuda daha yavaş olabilir
            
            # Zaten giriş yapılmış mı kontrol et
            if self.check_if_logged_in():
                print("✅ Zaten giriş yapılmış! (Profil kaydedilmiş)")
                return True
            
            print("🔑 Giriş bilgileri giriliyor...")
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
            
            # Login formu bekle ve doldur
            try:
                username_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_input = self.driver.find_element(By.NAME, "password")
                
                # Bilgileri temizle ve gir
                username_input.clear()
                time.sleep(0.5)
                username_input.send_keys(self.username)
                time.sleep(1)
                
                password_input.clear()
                time.sleep(0.5)
                password_input.send_keys(self.password)
                time.sleep(1)
                
                # Login butonuna tıkla
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
                print("✅ Login formu gönderildi")
                
            except Exception as e:
                print(f"❌ Login formu hatası: {e}")
                return False
            
            # Giriş sonucu bekle ve kontrol et
            for attempt in range(20):  # Bulut için daha uzun süre
                time.sleep(3)
                current_url = self.driver.current_url
                
                print(f"📍 Giriş kontrolü {attempt+1}/20: {current_url}")
                
                # 2FA gerekiyor mu?
                if "challenge" in current_url:
                    print("⚠️ 2FA/Challenge gerekiyor!")
                    if self.is_cloud:
                        print("❌ Bulut modda 2FA desteklenmiyor! Manuel giriş gerekli.")
                        return False
                    else:
                        print("🕐 2FA'yı manuel olarak tamamlayın (60 saniye)...")
                        for i in range(30):
                            time.sleep(2)
                            if "challenge" not in self.driver.current_url:
                                print("✅ 2FA tamamlandı!")
                                break
                
                # Başarılı giriş kontrolü
                if self.check_if_logged_in():
                    print("🎉 Giriş başarılı! Profil kaydedildi.")
                    self.is_logged_in = True
                    return True
                
                # Hata mesajı var mı?
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
        """Giriş yapılmış mı kontrol et"""
        try:
            current_url = self.driver.current_url
            
            # URL kontrolü
            if "login" in current_url or "accounts/login" in current_url:
                return False
            
            # DM linki var mı kontrol et
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
    
    def navigate_to_dms(self):
        """DM sayfasına git - Bulut optimize"""
        max_attempts = 5
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"📬 DM'e gidiliyor... (Deneme {attempt}/{max_attempts})")
                
                current_url = self.driver.current_url
                
                # Zaten DM'de miyiz?
                if "/direct/" in current_url:
                    print("✅ Zaten DM sayfasında!")
                    self.dismiss_popups()
                    return True
                
                # Login sayfasındaysak tekrar giriş yap
                if "login" in current_url:
                    print("⚠️ Oturum kapanmış, tekrar giriş yapılıyor...")
                    if self.login_once_safely():
                        continue
                    else:
                        return False
                
                # DM sayfasına git
                self.driver.get("https://www.instagram.com/direct/inbox/")
                time.sleep(5)  # Bulut için daha uzun bekle
                
                # Başarılı mı kontrol et
                if "/direct/" in self.driver.current_url:
                    print(f"✅ DM sayfasına ulaşıldı! (Deneme {attempt})")
                    self.dismiss_popups()
                    return True
                else:
                    print(f"❌ DM sayfasına ulaşılamadı (Deneme {attempt})")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ DM navigasyon hatası (Deneme {attempt}): {e}")
                time.sleep(2)
        
        print("❌ DM sayfasına ulaşılamadı! Tüm denemeler başarısız.")
        return False
    
    def dismiss_popups(self):
        """Pop-up'ları kapat - Bulut için güvenli"""
        popup_texts = [
            "Not Now", "Şimdi Değil", "Later", "Sonra", 
            "Turn on", "Aç", "Save", "Kaydet", "Cancel", "İptal"
        ]
        
        for text in popup_texts:
            try:
                # Metin bazlı arama
                buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                for btn in buttons:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(1)
                        print(f"✅ Popup kapatıldı: {text}")
                        break
            except:
                pass
        
        # Kapatma butonları
        close_selectors = [
            "//button[@aria-label='Close']",
            "//button[@aria-label='Kapat']",
            "//div[@role='button'][contains(@aria-label, 'Close')]"
        ]
        
        for selector in close_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for btn in buttons:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(1)
                        break
            except:
                pass
    
    def get_all_conversations(self):
        """Konuşmaları al - Bulut optimize"""
        try:
            print("🔍 Konuşmalar aranıyor...")
            
            # Sayfanın yüklenmesini bekle
            time.sleep(3)
            
            conversation_selectors = [
                "//div[@role='listitem']",
                "//div[@role='button'][.//img[@alt]]",
                "//a[contains(@href, '/direct/t/')]",
                "//div[contains(@class, 'conversation') or contains(@class, 'thread')]"
            ]
            
            conversations = []
            for selector in conversation_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements and len(elements) > 0:
                        conversations = elements
                        print(f"✅ {len(elements)} konuşma bulundu (selector: {selector})")
                        break
                except Exception as e:
                    print(f"❌ Selector hatası: {e}")
                    continue
            
            if not conversations:
                print("❌ Hiç konuşma bulunamadı!")
                return []
            
            valid_conversations = []
            
            for i, conv in enumerate(conversations[:10]):  # İlk 10 konuşmayı kontrol et
                try:
                    text = conv.text.strip()
                    if not text or len(text) < 3:
                        continue
                    
                    print(f"🔍 Konuşma {i+1}: {text[:80]}...")
                    
                    # Müzik/Note filtrele
                    if self.is_music_or_note_balloon(text):
                        print(f"🎵 Müzik/Note atlandı: {text[:30]}...")
                        continue
                    
                    # Yeni mesaj var mı kontrol et
                    if self.has_new_message(text):
                        valid_conversations.append(conv)
                        print(f"✅ Yeni mesaj bulundu: {text[:50]}...")
                    else:
                        print(f"🚫 Eski mesaj: {text[:50]}...")
                    
                except Exception as e:
                    print(f"❌ Konuşma kontrol hatası: {e}")
                    continue

            print(f"📊 Toplam: {len(conversations)} konuşma, {len(valid_conversations)} yeni mesaj")
            return valid_conversations
            
        except Exception as e:
            print(f"❌ Konuşma alma genel hatası: {e}")
            return []
    
    # Diğer metodlar aynı (is_music_or_note_balloon, has_new_message, vs.)
    def is_music_or_note_balloon(self, text):
        """Müzik/note balonu mu kontrol et"""
        try:
            text_lower = text.lower()
            
            note_keywords = [
                'note...', 'your note', 'add note', 'note',
                'add a note', 'create note'
            ]
            
            music_keywords = [
                'freedom', 'plutoski', 'future', 'song', 'music', 
                'album', 'track', 'artist', 'playlist',
                'shared a song', 'shared music'
            ]
            
            for keyword in note_keywords + music_keywords:
                if keyword in text_lower:
                    return True
            
            # Müzik formatı kontrolü
            lines = text.strip().split('\n')
            if len(lines) >= 2:
                first_line = lines[0].strip()
                if first_line.isupper() and len(first_line) < 20:
                    second_line = lines[1].strip()
                    if ',' in second_line:
                        return True
            
            return False
            
        except:
            return False
    
    def has_new_message(self, conversation_text):
        """Gerçekten yeni mesaj var mı kontrol et"""
        try:
            text = conversation_text.lower()
            
            # Bizim mesajımızsa geç
            if 'you:' in text or 'sen:' in text:
                return False
            
            # Sadece activity status varsa geç
            activity_patterns = [
                'active now', 'active just now', 'active 1m ago', 'active 2m ago', 
                'active 3m ago', 'active 4m ago', 'active 5m ago', 'active 10m ago',
                'active 15m ago', 'active 30m ago', 'active 1h ago', 'active 2h ago'
            ]
            
            has_activity = any(pattern in text for pattern in activity_patterns)
            
            if has_activity:
                # Activity'yi çıkarınca geriye ne kalıyor?
                cleaned = text
                for pattern in activity_patterns:
                    cleaned = cleaned.replace(pattern, '').strip()
                
                if len(cleaned.split()) <= 2:
                    return False
            
            # Typing durumu
            if 'typing' in text and len(conversation_text.strip()) < 40:
                return False
            
            # Yakın zaman göstergeleri
            recent_indicators = ['now', 'just now', '1m', '2m', '3m', '1s', '2s', '30s']
            has_recent = any(indicator in text for indicator in recent_indicators if 'active' not in text)
            
            # Mesaj formatı (· veya • işaretleri)
            has_message_format = ('·' in conversation_text or '•' in conversation_text) and not has_activity
            
            if has_recent or has_message_format:
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Mesaj kontrol hatası: {e}")
            return False
    
    def open_conversation(self, conv_element):
        """Konuşmayı aç"""
        try:
            print("📂 Konuşma açılıyor...")
            
            # Elemente scroll yap
            self.driver.execute_script("arguments[0].scrollIntoView(true);", conv_element)
            time.sleep(1)
            
            # Tıkla
            conv_element.click()
            time.sleep(3)  # Bulut için daha uzun bekle
            
            # Açıldı mı kontrol et
            current_url = self.driver.current_url
            if "/direct/t/" in current_url:
                print("✅ Konuşma açıldı!")
                return True
            else:
                print(f"❌ Konuşma açılamadı! URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Konuşma açma hatası: {e}")
            return False
    
    def analyze_conversation(self):
        """Konuşmayı analiz et"""
        try:
            conv_id = self.driver.current_url.split('/')[-2] if '/direct/t/' in self.driver.current_url else "unknown"
            
            # Mesajları bul
            message_selectors = [
                "//div[@data-testid='conversation-message']//span",
                "//span[@dir='auto'][not(ancestor::header)][not(ancestor::nav)]",
                "//div[@role='none']//span[@dir='auto']"
            ]
            
            all_messages = []
            for selector in message_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 1:
                            all_messages.append(text)
                    if all_messages:
                        break
                except:
                    continue
            
            # Gereksiz mesajları filtrele
            cleaned_messages = []
            skip_keywords = ['seen', 'delivered', 'active', 'typing', 'online']
            
            for msg in all_messages:
                if any(skip in msg.lower() for skip in skip_keywords):
                    continue
                if len(msg.strip()) < 2:
                    continue
                cleaned_messages.append(msg)
            
            # Son 15 mesajı al
            recent_messages = cleaned_messages[-15:] if len(cleaned_messages) > 15 else cleaned_messages
            
            # Konuşma geçmişini güncelle
            if conv_id not in self.conversation_history:
                self.conversation_history[conv_id] = []
            
            new_history = []
            for msg in recent_messages:
                if self.is_our_message(msg):
                    clean_msg = self.clean_our_message(msg)
                    if clean_msg:
                        new_history.append({"role": "assistant", "content": clean_msg})
                else:
                    new_history.append({"role": "user", "content": msg})
            
            self.conversation_history[conv_id] = new_history[-15:]
            
            print(f"🔬 Analiz: {len(recent_messages)} mesaj, {len(self.conversation_history[conv_id])} geçmiş")
            
            return [{'sender': 'other_user', 'message': msg} for msg in recent_messages]
            
        except Exception as e:
            print(f"❌ Analiz hatası: {e}")
            return []
    
    def is_our_message(self, message):
        """Bu mesaj bizim mi kontrol et"""
        message_lower = message.lower()
        
        if any(indicator in message_lower for indicator in ['you:', 'sen:', 'siz:']):
            return True
        
        if message.startswith('You:') or message.startswith('you:'):
            return True
        
        return False
    
    def clean_our_message(self, message):
        """Bizim mesajımızdan gereksiz kısımları temizle"""
        cleaned = message
        prefixes = ['You:', 'you:', 'Sen:', 'sen:', 'Siz:', 'siz:']
        
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        if '·' in cleaned:
            cleaned = cleaned.split('·')[0].strip()
        
        return cleaned if len(cleaned) > 1 else None
    
    def find_unanswered_messages(self, messages):
        """Cevaplanmamış mesajları bul"""
        conv_id = self.driver.current_url.split('/')[-2] if '/direct/t/' in self.driver.current_url else "unknown"
        
        if conv_id not in self.processed_messages:
            self.processed_messages[conv_id] = set()
        
        unanswered = []
        for msg_data in messages[-3:]:  # Son 3 mesajı kontrol et
            sender = msg_data['sender']
            message = msg_data['message']
            
            msg_key = f"{sender}:{message}"
            
            if sender != self.username and msg_key not in self.processed_messages[conv_id]:
                unanswered.append(msg_data)
        
        return unanswered
    
    def get_ai_response(self, message, sender):
        """DeepSeek API ile akıllı cevap üret"""
        if not self.deepseek_api_key:
            print("⚠️ DeepSeek API key yok, rastgele cevap kullanılıyor")
            return self.get_random_response(message, sender)
        
        try:
            print(f"🤖 DeepSeek'ten akıllı cevap isteniyor...")
            
            from openai import OpenAI
            client = OpenAI(
                api_key=self.deepseek_api_key, 
                base_url="https://api.deepseek.com"
            )
            
            conv_id = self.driver.current_url.split('/')[-2] if '/direct/t/' in self.driver.current_url else "unknown"
            
            system_prompt = """Sen Instagram'da samimi konuşan arkadaşsın. Sohbet geçmişini dikkate alarak uygun cevap ver.
Bazen küfür et ama dengeli ol, samimi ve doğal cevap ver. EMOJİ KULLANMA! Sadece normal harfler kullan. 
Türkçe konuş. Max 3 cümle. Sohbetin akışına uygun ol."""
            
            conversation_messages = []
            if conv_id in self.conversation_history and self.conversation_history[conv_id]:
                recent_history = self.conversation_history[conv_id][-10:]
                conversation_messages.extend(recent_history)
            
            conversation_messages.append({
                "role": "user",
                "content": message
            })
            
            api_messages = [{"role": "system", "content": system_prompt}]
            api_messages.extend(conversation_messages)
            
            print(f"📚 {len(conversation_messages)} mesajlık geçmişle birlikte gönderiliyor...")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=api_messages,
                max_tokens=450,
                temperature=0.7,
                stream=False
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            if not ai_response or len(ai_response) < 2:
                print("⚠️ DeepSeek boş cevap döndürdü, rastgele cevap kullanılıyor")
                return self.get_random_response(message, sender)
            
            print(f"✅ DeepSeek cevabı: {ai_response}")
            
            cleaned_response = self.clean_message_for_chrome(ai_response)
            print(f"🧹 Temizlenmiş cevap: {cleaned_response}")
            
            # Konuşma geçmişini güncelle
            if conv_id not in self.conversation_history:
                self.conversation_history[conv_id] = []
            
            self.conversation_history[conv_id].append({
                "role": "user",
                "content": message
            })
            
            self.conversation_history[conv_id].append({
                "role": "assistant", 
                "content": cleaned_response
            })
            
            # Geçmişi 20 mesajla sınırla
            if len(self.conversation_history[conv_id]) > 20:
                self.conversation_history[conv_id] = self.conversation_history[conv_id][-20:]
            
            return cleaned_response
            
        except Exception as e:
            print(f"❌ DeepSeek API hatası: {e}")
            return self.get_random_response(message, sender)
    
    def clean_message_for_chrome(self, message):
        """Chrome'un desteklemediği karakterleri temizle"""
        try:
            # Emoji pattern
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                u"\U00002702-\U000027B0"  # dingbats
                u"\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE)
            
            cleaned = emoji_pattern.sub('', message)
            
            # Özel karakterleri temizle
            cleaned = cleaned.replace('✨', '').replace('😏', '').replace('🔥', '').replace('💯', '')
            cleaned = cleaned.replace('"', '').replace('"', '').replace('"', '')
            cleaned = cleaned.strip()
            
            if not cleaned or len(cleaned) < 2:
                return "hey whats up"
            
            return cleaned
            
        except Exception as e:
            print(f"❌ Mesaj temizleme hatası: {e}")
            return "sup"
    
    def get_random_response(self, message, sender):
        """Rastgele cevap üret"""
        responses = [
            "hey whats up",
            "yo!",
            "sup",
            "hey there",
            "wassup bro",
            "yooo",
            "hi!",
            "how's it going",
            "what's good",
            "hello!"
        ]
        return random.choice(responses)
    
    def send_reply(self, message):
        """Mesaj gönder - Bulut optimize"""
        try:
            print(f"📤 Mesaj gönderiliyor: {message}")
            
            # Input alanını bul
            input_selectors = [
                "//textarea[@placeholder='Message...']",
                "//div[@contenteditable='true'][@aria-label='Message']",
                "//div[@contenteditable='true'][@role='textbox']",
                "//textarea[@aria-label='Message']"
            ]
            
            text_input = None
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            text_input = elem
                            break
                    if text_input:
                        break
                except:
                    continue
            
            if not text_input:
                print("❌ Mesaj input'u bulunamadı!")
                return False
            
            # Mesajı gönder
            text_input.click()
            time.sleep(0.5)
            text_input.clear()
            time.sleep(0.3)
            text_input.send_keys(message)
            time.sleep(0.5)
            text_input.send_keys(Keys.ENTER)
            
            print(f"✅ Gönderildi: {message}")
            time.sleep(2)  # Gönderim sonrası bekle
            return True
            
        except Exception as e:
            print(f"❌ Gönderme hatası: {e}")
            return False
    
    def process_conversation(self):
        """Konuşmayı işle"""
        try:
            messages = self.analyze_conversation()
            
            if not messages:
                print("❌ Mesaj bulunamadı")
                return False
            
            unanswered = self.find_unanswered_messages(messages)
            
            if not unanswered:
                print("✅ Tüm mesajlar cevaplanmış")
                return False
            
            print(f"📨 {len(unanswered)} cevaplanmamış mesaj var")
            
            conv_id = self.driver.current_url.split('/')[-2] if '/direct/t/' in self.driver.current_url else "unknown"
            first_unanswered = unanswered[0]
            sender = first_unanswered['sender']
            message = first_unanswered['message']
            
            print(f"💬 CEVAP VERİLECEK: {message}")
            
            response = self.get_ai_response(message, sender)
            
            if self.send_reply(response):
                if conv_id not in self.processed_messages:
                    self.processed_messages[conv_id] = set()
                
                for msg_data in unanswered:
                    msg_sender = msg_data['sender']
                    msg_content = msg_data['message']
                    msg_key = f"{msg_sender}:{msg_content}"
                    self.processed_messages[conv_id].add(msg_key)
                    print(f"✅ İşaretlendi: {msg_key}")
                
                print("✅ Mesaj gönderildi ve konuşma işaretlendi!")
                return True
            else:
                print("❌ Mesaj gönderilemedi!")
                return False
            
        except Exception as e:
            print(f"❌ İşleme hatası: {e}")
            return False
    
    def run(self):
        """Ana bot döngüsü - Bulut optimize"""
        print("🚀 INSTAGRAM DM BOT BAŞLATIYOR (BULUT MOD)...")
        print("="*60)
        
        if self.is_cloud:
            print("☁️ BULUT SUNUCU MODU AKTİF!")
            print("🖥️ Headless Chrome kullanılıyor")
            print("💾 Düşük RAM optimizasyonu aktif")
        
        try:
            # Chrome başlat
            self.setup_chrome_driver()
            
            # Giriş yap (tek seferlik)
            if not self.login_once_safely():
                print("❌ Giriş başarısız!")
                return
            
            # DM sayfasına git
            if not self.navigate_to_dms():
                print("❌ DM sayfasına ulaşılamadı!")
                return
            
            print("\n✅ BOT HAZIR! Mesaj takibi başlıyor...")
            print("🔄 Kontrol döngüsü: Her 5 saniyede bir")
            print("="*60)
            
            check_count = 0
            consecutive_errors = 0
            max_errors = 5
            
            while True:
                check_count += 1
                
                try:
                    # Oturum kontrolü
                    current_url = self.driver.current_url
                    if "login" in current_url:
                        print("⚠️ Oturum süresi dolmuş, yeniden giriş...")
                        if self.login_once_safely() and self.navigate_to_dms():
                            print("✅ Oturum yenilendi!")
                            consecutive_errors = 0
                        else:
                            consecutive_errors += 1
                            if consecutive_errors >= max_errors:
                                print("❌ Çok fazla giriş hatası, bot durduruluyor!")
                                break
                            continue
                    
                    # DM sayfası kontrolü
                    if "/direct/" not in current_url:
                        print("⚠️ DM sayfasında değiliz, yönlendiriliyor...")
                        if not self.navigate_to_dms():
                            consecutive_errors += 1
                            if consecutive_errors >= max_errors:
                                print("❌ DM sayfasına ulaşılamıyor, bot durduruluyor!")
                                break
                            continue
                        consecutive_errors = 0
                    
                    # Konuşmaları kontrol et
                    print(f"\n🔍 Kontrol #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
                    conversations = self.get_all_conversations()
                    
                    if conversations:
                        print(f"🚨 {len(conversations)} aktif konuşma bulundu!")
                        
                        processed_any = False
                        for i, conv in enumerate(conversations):
                            try:
                                print(f"📂 Konuşma {i+1}/{len(conversations)} açılıyor...")
                                
                                if self.open_conversation(conv):
                                    if self.process_conversation():
                                        print("✅ Mesaj gönderildi ve işaretlendi!")
                                        processed_any = True
                                    
                                    # Geri ana sayfaya dön
                                    self.driver.get("https://www.instagram.com/direct/inbox/")
                                    time.sleep(2)
                                    
                                    # Bir mesaj işlediysen dur (spam önleme)
                                    if processed_any:
                                        break
                                
                            except Exception as e:
                                print(f"❌ Konuşma işleme hatası: {e}")
                                # Ana sayfaya dön
                                self.driver.get("https://www.instagram.com/direct/inbox/")
                                time.sleep(2)
                                continue
                        
                        consecutive_errors = 0  # Başarılı işlem
                        
                    else:
                        # Mesaj yok
                        if check_count == 1:
                            print("👂 Bot dinlemede... (yeni mesaj geldiğinde aktivleşecek)")
                        elif check_count % 20 == 0:  # Her 20 kontrolde bir bilgi ver
                            print(f"😴 Sessiz... ({check_count}. kontrol) - {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Bekleme süresi
                    if self.is_cloud:
                        time.sleep(5)  # Bulutta daha uzun bekle (kaynak tasarrufu)
                    else:
                        time.sleep(3)  # Yerel geliştirmede hızlı
                
                except Exception as e:
                    consecutive_errors += 1
                    print(f"❌ Kontrol hatası ({consecutive_errors}/{max_errors}): {e}")
                    
                    if consecutive_errors >= max_errors:
                        print("❌ Çok fazla hata! Bot durduruluyor...")
                        break
                    
                    # Ana sayfaya dön ve devam et
                    try:
                        self.driver.get("https://www.instagram.com/direct/inbox/")
                        time.sleep(3)
                    except:
                        pass
                
        except KeyboardInterrupt:
            print("\n🛑 BOT MANUEL OLARAK DURDURULDU!")
        except Exception as e:
            print(f"\n❌ BOT GENEL HATASI: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("👋 Chrome kapatıldı!")
                except:
                    pass
            print("🏁 Bot sonlandırıldı!")

# ===== BULUT DEPLOYMENT İÇİN YARDıMCı KODLAR =====

def create_requirements_txt():
    """requirements.txt dosyası oluştur"""
    requirements = """selenium==4.15.0
webdriver-manager==3.8.6
openai==1.3.0
requests==2.31.0
flask==2.3.3
"""
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("✅ requirements.txt oluşturuldu!")

def create_dockerfile():
    """Dockerfile oluştur"""
    dockerfile = """FROM python:3.9-slim

# Sistem paketleri
RUN apt-get update && apt-get install -y \\
    wget \\
    gnupg \\
    unzip \\
    curl \\
    xvfb

# Chrome repository ekle
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \\
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \\
    && apt-get update \\
    && apt-get install -y google-chrome-stable

# ChromeDriver kurulumu
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \\
    mkdir -p /opt/chromedriver-$CHROMEDRIVER_VERSION && \\
    curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/104.0.5112.79/chromedriver_linux64.zip && \\
    unzip -qq /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION && \\
    rm /tmp/chromedriver_linux64.zip && \\
    chmod +x /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver && \\
    ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver /usr/local/bin/chromedriver

# Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Bot kodları
COPY . /app
WORKDIR /app

# Çalıştır
CMD ["python", "cloud_instagram_bot.py"]
"""
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    print("✅ Dockerfile oluşturuldu!")

# Ana çalıştırma
if __name__ == "__main__":
    # Environment variables'dan config al (bulut için güvenli)
    config = {
        'username': os.environ.get('INSTAGRAM_USERNAME'),
        'password': os.environ.get('INSTAGRAM_PASSWORD'),
        'deepseek_api_key': os.environ.get('DEEPSEEK_API_KEY'),
        'is_cloud': os.environ.get('IS_CLOUD', 'false').lower() == 'true'
    }
    
    # Gerekli bilgiler eksik mi kontrol et
    if not config['username']:
        print("❌ INSTAGRAM_USERNAME environment variable eksik!")
        exit(1)
    if not config['password']:
        print("❌ INSTAGRAM_PASSWORD environment variable eksik!")
        exit(1)
    if not config['deepseek_api_key']:
        print("⚠️ DEEPSEEK_API_KEY eksik! Rastgele cevaplar kullanılacak.")
    
    print(f"✅ Instagram kullanıcısı: {config['username']}")
    print(f"✅ DeepSeek API: {'Aktif' if config['deepseek_api_key'] else 'Deaktif'}")
    
    print("🚀 BULUT HAZIR INSTAGRAM DM BOT + DEEPSEEK AI")
    print("☁️ HEADLESS CHROME DESTEĞİ")
    print("🔒 TEK SEFERLİK GİRİŞ SİSTEMİ")
    print("🎯 SADECE GERÇEK YENİ MESAJLARA CEVAP VERİR")
    print("🤖 AKILLI SOHBET GEÇMİŞİ SISTEMI")
    print("💰 DEEPSEEK API - ÇOOK UCUZ!")
    print("="*60)
    
    if config['is_cloud']:
        print("☁️ BULUT MODU AKTİF!")
        print("🖥️ Headless Chrome kullanılacak")
    else:
        print("💻 YEREL GELIŞTIRME MODU")
        print("🖥️ Görsel Chrome kullanılacak")
    
    if config['deepseek_api_key']:
        print("✅ DeepSeek API key bulundu!")
        print("💡 Ayda sadece 30 cent harcar!")
    else:
        print("⚠️ UYARI: DeepSeek API key girilmedi!")
        print("🔄 Rastgele cevaplar kullanılacak")
    
    print("="*60)
    
    # Bot'u başlat
    bot = CloudInstagramDMBot(config)
    bot.run()