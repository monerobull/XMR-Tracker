import requests
from PIL import Image, ImageDraw, ImageFont
import time
import io
from datetime import datetime

# --- CONFIGURATION ---
DEVICE_IP = "enter_IP_here"
CRYPTO_ID = "monero"
CURRENCY = "eur"
UPDATE_INTERVAL = 60  # Faster update makes the timer more accurate but reduces the lifetime of your SmallTV.
# ---------------------

last_price = 0

def get_crypto_price():
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO_ID}&vs_currencies={CURRENCY}"
        r = requests.get(url, timeout=10)
        return r.json()[CRYPTO_ID][CURRENCY]
    except:
        return None

def get_block_data():
    """Fetches height and timestamp of the latest block."""
    sources = [
        "https://p2pool.io/api/network/stats",
        "https://xmrchain.net/api/networkinfo"
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json()
            # Handle p2pool format
            if 'height' in data and 'timestamp' in data:
                return data['height'], data['timestamp']
            # Handle xmrchain format (nested in 'data')
            if 'data' in data:
                return data['data']['height'], data['data']['timestamp']
        except:
            continue
    return None, None

def create_image(price, height, block_time):
    global last_price
    img = Image.new('RGB', (240, 240), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Color Logic for Price
    price_color = (0, 255, 100) # Green
    if last_price > 0 and price < last_price:
        price_color = (255, 50, 50) # Red
    last_price = price

    # Calculate time since last block
    now = int(time.time())
    seconds_ago = now - block_time
    minutes = seconds_ago // 60
    seconds = seconds_ago % 60
    time_str = f"{minutes}m {seconds}s ago"

    # Load Fonts
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 34)
        font_sub = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 22)
        font_tiny = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 18)
    except:
        font_main = font_sub = font_tiny = ImageFont.load_default()

    # 1. Header
    draw.text((20, 20), "MONERO (XMR)", fill=(120, 120, 120), font=font_tiny)

    # 2. Price (Smaller than before to fit more data)
    draw.text((20, 50), f"€{price:,.2f}", fill=price_color, font=font_main)

    # 3. Block Height
    draw.text((20, 115), "BLOCK HEIGHT", fill=(120, 120, 120), font=font_tiny)
    draw.text((20, 140), f"{height:,}", fill=(255, 255, 255), font=font_sub)

    # 4. Time Since Last Block
    draw.text((20, 185), "LAST BLOCK", fill=(120, 120, 120), font=font_tiny)
    draw.text((20, 210), time_str, fill=(200, 150, 255), font=font_sub)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

def upload(image_bytes):
    url = f"http://{DEVICE_IP}/doUpload?dir=/image/"
    files = {'file': ('crypto.jpg', image_bytes, 'image/jpeg')}
    try:
        r = requests.post(url, files=files, timeout=5)
        return r.status_code == 200
    except:
        return False

print(f"Starting Pro XMR Ticker for {DEVICE_IP}...")

while True:
    price = get_crypto_price()
    height, b_time = get_block_data()

    if price and height and b_time:
        img_data = create_image(price, height, b_time)
        if upload(img_data):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] XMR: €{price} | Height: {height}")
    else:
        print("Data fetch failed. Retrying...")

    time.sleep(UPDATE_INTERVAL)
