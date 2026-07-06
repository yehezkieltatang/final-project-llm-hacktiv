"""
Screenshot script for SIEMGuard using Selenium.
Captures real chat interactions with sample events and AI responses.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

SCREENSHOT_DIR = "assets"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshot(driver, name, wait_time=2):
    time.sleep(wait_time)
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"[OK] {path}")
    return path

def find_chat_input(driver):
    strategies = [
        (By.CSS_SELECTOR, "textarea[data-testid='stChatInput']"),
        (By.CSS_SELECTOR, "input[data-testid='stChatInput']"),
        (By.CSS_SELECTOR, ".stChatInput textarea"),
        (By.CSS_SELECTOR, ".stChatInput input"),
        (By.TAG_NAME, "textarea"),
        (By.TAG_NAME, "input"),
    ]
    for by, selector in strategies:
        try:
            elements = driver.find_elements(by, selector)
            for el in elements:
                if el.is_displayed():
                    return el
        except:
            continue
    return None

def send_message(driver, text):
    chat_input = find_chat_input(driver)
    if not chat_input:
        print("[WARN] Chat input not found")
        return False
    driver.execute_script("arguments[0].scrollIntoView(true);", chat_input)
    time.sleep(0.5)
    chat_input.click()
    time.sleep(0.3)
    chat_input.clear()
    chat_input.send_keys(text)
    time.sleep(0.5)
    chat_input.send_keys(Keys.ENTER)
    print(f"[SENT] '{text[:60]}...'")
    return True

def main():
    print("[START] Taking screenshots with sample event interactions...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1400,900")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # ====== 1. MAIN PAGE ======
        print("\n[1/6] Main page...")
        driver.get("http://localhost:8501")
        time.sleep(5)
        take_screenshot(driver, "screenshot_main")
        
        # ====== 2. SIDEBAR ======
        print("\n[2/6] Sidebar...")
        time.sleep(1)
        take_screenshot(driver, "screenshot_sidebar")
        
        # ====== 3. LOAD SAMPLE EVENT VIA SIDEBAR ======
        print("\n[3/6] Loading sample event from sidebar...")
        try:
            # Find the "Load to Chat" button in sidebar
            load_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Load to Chat') or contains(text(), 'Muat ke Chat')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", load_btn)
            time.sleep(0.5)
            load_btn.click()
            print("[OK] Clicked Load to Chat button")
            time.sleep(3)
        except Exception as e:
            print(f"[WARN] Could not click Load to Chat: {e}")
        
        # Wait for AI to analyze the event
        print("[WAIT] Waiting for AI event analysis (25 seconds)...")
        time.sleep(25)
        take_screenshot(driver, "screenshot_sample_event")
        
        # ====== 4. ASK FOLLOW-UP QUESTION ======
        print("\n[4/6] Asking follow-up question about the event...")
        if send_message(driver, "What is the severity level of this event and should we be concerned?"):
            print("[WAIT] Waiting for follow-up response (20 seconds)...")
            time.sleep(20)
        take_screenshot(driver, "screenshot_followup")
        
        # ====== 5. SWITCH TO INDONESIAN ======
        print("\n[5/6] Switching to Indonesian...")
        try:
            labels = driver.find_elements(By.TAG_NAME, "label")
            for label in labels:
                if "Indonesia" in label.text:
                    driver.execute_script("arguments[0].scrollIntoView(true);", label)
                    time.sleep(0.3)
                    label.click()
                    print("[OK] Switched to Indonesian")
                    time.sleep(3)
                    break
        except Exception as e:
            print(f"[WARN] Language switch: {e}")
        
        take_screenshot(driver, "screenshot_indonesia")
        
        # ====== 6. ASK IN INDONESIAN ======
        print("\n[6/6] Asking in Indonesian about security event...")
        if send_message(driver, "Analisis event dengan signature 'SURICATA STREAM Packet with broken ack' dan jelaskan dampaknya"):
            print("[WAIT] Waiting for Indonesian analysis (20 seconds)...")
            time.sleep(20)
        take_screenshot(driver, "screenshot_indonesia_chat")
        
        print("\n[DONE] All screenshots captured!")
        for f in sorted(os.listdir(SCREENSHOT_DIR)):
            if f.endswith('.png'):
                size = os.path.getsize(os.path.join(SCREENSHOT_DIR, f))
                print(f"  - {f} ({size/1024:.1f} KB)")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()