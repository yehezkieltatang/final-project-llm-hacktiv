"""
Screenshot script for SIEMGuard using Selenium.
Takes screenshots of the application UI in various states.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

SCREENSHOT_DIR = "assets"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshot(driver, name, wait_time=2):
    time.sleep(wait_time)
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"[OK] {path}")
    return path

def inject_chat_message(driver, role, content):
    """Inject a chat message into the Streamlit DOM for screenshot purposes."""
    js = """
    // Find the chat message container
    const main = document.querySelector('.stMain');
    if (!main) return false;
    
    // Create a chat message element
    const msgDiv = document.createElement('div');
    msgDiv.setAttribute('data-testid', arguments[0] === 'user' ? 'user-message' : 'assistant-message');
    msgDiv.className = 'stChatMessage';
    msgDiv.style.cssText = 'background-color: ' + (arguments[0] === 'user' ? '#1E2A3A' : '#1A1D27') + '; border: 1px solid ' + (arguments[0] === 'user' ? '#00FFAA33' : '#FF6B6B33') + '; border-radius: 8px; padding: 12px; margin: 8px 0;';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'stMarkdown';
    contentDiv.innerHTML = arguments[1];
    
    msgDiv.appendChild(contentDiv);
    
    // Insert before the chat input area
    const chatInput = document.querySelector('[data-testid="stChatInput"]') || document.querySelector('textarea') || document.querySelector('input[type="text"]');
    if (chatInput) {
        chatInput.closest('.stChatInput')?.before(msgDiv) || chatInput.parentElement?.before(msgDiv);
    } else {
        main.appendChild(msgDiv);
    }
    return true;
    """
    try:
        driver.execute_script(js, role, content)
        return True
    except:
        return False

def main():
    print("[START] Taking screenshots...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1400,900")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 1. Main page - English welcome
        print("\n[1/5] Main page...")
        driver.get("http://localhost:8501")
        time.sleep(5)
        take_screenshot(driver, "screenshot_main")
        
        # 2. Sidebar visible
        print("\n[2/5] Sidebar...")
        time.sleep(1)
        take_screenshot(driver, "screenshot_sidebar")
        
        # 3. Inject a sample chat interaction
        print("\n[3/5] Chat interaction...")
        inject_chat_message(driver, "user", 
            "<p>Please analyze this security event:</p>"
            "<pre><code>{\n  \"alert_signature\": \"ET INFO SSH session in progress on Expected Port\",\n  \"alert_severity\": 3,\n  \"src_ip\": \"40.83.182.122\",\n  \"dest_ip\": \"103.122.32.67\",\n  \"proto\": \"TCP\",\n  \"dest_port\": 22\n}</code></pre>"
        )
        time.sleep(0.5)
        inject_chat_message(driver, "assistant",
            "<h3>🔍 Event Analysis</h3>"
            "<p><strong>Summary:</strong> SSH session detected from <strong>Microsoft Azure (US)</strong> to <strong>Jakarta server</strong> on port 22.</p>"
            "<p><strong>Severity:</strong> 🟡 <strong>Level 3</strong> (Informational) - Low risk</p>"
            "<p><strong>MITRE ATT&CK:</strong> <code>TA0008</code> - Lateral Movement / <code>T1021.004</code> - SSH</p>"
            "<p><strong>Cyber Kill Chain:</strong> Reconnaissance</p>"
            "<p><strong>Recommendation:</strong> Monitor for unusual SSH patterns. This appears to be normal SSH traffic.</p>"
        )
        time.sleep(1)
        take_screenshot(driver, "screenshot_chat")
        
        # 4. Switch to Indonesian
        print("\n[4/5] Indonesian language...")
        try:
            radio_group = driver.find_element(By.CSS_SELECTOR, "div[data-testid='stSidebar']")
            labels = radio_group.find_elements(By.TAG_NAME, "label")
            for label in labels:
                if "Indonesia" in label.text:
                    driver.execute_script("arguments[0].scrollIntoView(true);", label)
                    time.sleep(0.3)
                    label.click()
                    print("[DEBUG] Switched to Indonesian")
                    time.sleep(3)
                    break
        except Exception as e:
            print(f"[WARN] Language switch failed: {e}")
        
        take_screenshot(driver, "screenshot_indonesia")
        
        # 5. Indonesian with chat
        print("\n[5/5] Indonesian chat...")
        inject_chat_message(driver, "user",
            "<p>Jelaskan event keamanan ini:</p>"
            "<pre><code>{\n  \"alert_signature\": \"SURICATA STREAM Packet with broken ack\",\n  \"alert_severity\": 3,\n  \"src_ip\": \"103.78.114.53\",\n  \"dest_port\": 445,\n  \"proto\": \"TCP\"\n}</code></pre>"
        )
        time.sleep(0.5)
        inject_chat_message(driver, "assistant",
            "<h3>🔍 Analisis Event</h3>"
            "<p><strong>Ringkasan:</strong> Paket TCP dengan <em>broken acknowledgment</em> terdeteksi dari IP lokal Jakarta menuju port <strong>445 (SMB)</strong>.</p>"
            "<p><strong>Tingkat Keparahan:</strong> 🟡 <strong>Level 3</strong> (Informational)</p>"
            "<p><strong>MITRE ATT&CK:</strong> <code>TA0043</code> - Reconnaissance / <code>T1595</code> - Active Scanning</p>"
            "<p><strong>Cyber Kill Chain:</strong> Reconnaissance</p>"
            "<p><strong>Rekomendasi:</strong> Periksa apakah ada scanning SMB yang mencurigakan dari IP internal.</p>"
        )
        time.sleep(1)
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