# telegram_bot.py - Apple Stock Telegram Bot
import os
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from threading import Thread, Lock
import re

# ============================================
# TELEGRAM BOT CONFIGURATION
# ============================================

# ✅ Environment variable से Token लें (सुरक्षित)
BOT_TOKEN = os.environ.get('8753779153:AAFDvwJIOOtgjtg4lYQ4DciHQ4rSC1eSzCA')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

# ✅ Environment variable से Authorized Users लें (Optional)
AUTHORIZED_USERS_STR = os.environ.get('AUTHORIZED_USERS', '')
AUTHORIZED_USERS = [uid.strip() for uid in AUTHORIZED_USERS_STR.split(',') if uid.strip()] if AUTHORIZED_USERS_STR else []

# 👑 Admin Users
ADMIN_USERS = [
    "717832291",  # Your User ID - ADMIN
]

# 🔓 Open/Closed Mode
ALLOW_ALL_USERS = os.environ.get('ALLOW_ALL_USERS', 'False').lower() == 'true'

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# APPLE STORE CHECKER CLASS
# ============================================

class AppleStoreChecker:
    def __init__(self):
        self.base_url = "https://www.apple.com/in/shop/pickup-message-recommendations"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,hi;q=0.7',
            'Referer': 'https://www.apple.com/in/shop/buy-iphone/iphone-17/6.3%22-display-256gb-white',
        }
        
        # iPhone 17 256GB Colors with SKUs
        self.colors = {
            'Lavender': {'sku': 'MG6M4HN/A', 'emoji': '🟣'},
            'Sage': {'sku': 'MG6N4HN/A', 'emoji': '🟢'},
            'Mist Blue': {'sku': 'MG6L4HN/A', 'emoji': '🔵'},
            'White': {'sku': 'MG6K4HN/A', 'emoji': '⚪'},
            'Black': {'sku': 'MG6J4HN/A', 'emoji': '⚫'}
        }
        
        # Store codes
        self.stores = {
            'Saket': {'code': 'R756', 'city': 'Delhi'},
            'Noida': {'code': 'R787', 'city': 'Noida'},
            'BKC': {'code': 'R744', 'city': 'Mumbai'},
            'Borivali': {'code': 'R757', 'city': 'Mumbai'},
            'Hebbal': {'code': 'R790', 'city': 'Bangalore'},
            'Koregaon Park': {'code': 'R788', 'city': 'Pune'}
        }
    
    def check_product(self, product_sku, store_code):
        """Check product availability at specific store"""
        params = {
            'fae': 'true',
            'mts.0': 'regular',
            'mts.1': 'compact',
            'searchNearby': 'true',
            'store': store_code,
            'product': product_sku
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data, product_sku)
            else:
                return {'in_stock': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'in_stock': False, 'error': str(e)}
    
    def _parse_response(self, data, sku):
        """Parse API response"""
        try:
            body = data.get('body', {})
            pickup = body.get('PickupMessage', {})
            stores = pickup.get('stores', [])
            
            for store in stores:
                parts = store.get('partsAvailability', {})
                if sku in parts:
                    avail = parts[sku]
                    if isinstance(avail, dict):
                        return {
                            'in_stock': avail.get('available', False),
                            'pickup_date': avail.get('pickupWindow', 'Available')
                        }
            
            return {'in_stock': False, 'pickup_date': None}
            
        except Exception as e:
            return {'in_stock': False, 'error': f'Parse error: {str(e)}'}
    
    def check_all_stores_all_colors(self):
        """Check all colors at all stores"""
        available = []
        
        for color_name, color_info in self.colors.items():
            for store_name, store_info in self.stores.items():
                result = self.check_product(color_info['sku'], store_info['code'])
                
                if result.get('in_stock'):
                    available.append({
                        'color': color_name,
                        'sku': color_info['sku'],
                        'store': store_name,
                        'city': store_info['city'],
                        'pickup_date': result.get('pickup_date', 'Available')
                    })
                
                time.sleep(0.2)
        
        return available
    
    def check_color_all_stores(self, color_name):
        """Check specific color at all stores"""
        if color_name not in self.colors:
            return None
        
        color_info = self.colors[color_name]
        available_stores = []
        
        for store_name, store_info in self.stores.items():
            result = self.check_product(color_info['sku'], store_info['code'])
            
            if result.get('in_stock'):
                available_stores.append({
                    'store': store_name,
                    'city': store_info['city'],
                    'pickup_date': result.get('pickup_date', 'Available')
                })
            
            time.sleep(0.2)
        
        return available_stores
    
    def check_all_colors_specific_store(self, store_name):
        """Check all colors at specific store"""
        if store_name not in self.stores:
            return None
        
        store_info = self.stores[store_name]
        available_colors = []
        
        for color_name, color_info in self.colors.items():
            result = self.check_product(color_info['sku'], store_info['code'])
            
            if result.get('in_stock'):
                available_colors.append({
                    'color': color_name,
                    'pickup_date': result.get('pickup_date', 'Available')
                })
            
            time.sleep(0.2)
        
        return available_colors
    
    def test_api_status(self):
        """Test if API is working"""
        test_sku = 'MG6M4HN/A'
        test_store = 'R756'
        
        try:
            start_time = time.time()
            result = self.check_product(test_sku, test_store)
            response_time = time.time() - start_time
            
            return {
                'working': not result.get('error'),
                'response_time': round(response_time, 2),
                'error': result.get('error')
            }
        except Exception as e:
            return {'working': False, 'error': str(e)}


# ============================================
# TELEGRAM BOT CLASS
# ============================================

class TelegramStockBot:
    def __init__(self):
        self.checker = AppleStoreChecker()
        self.last_update_id = 0
        
        # Store monitoring threads per user
        self.monitoring_threads = {}
        self.monitoring_lock = Lock()
        self.running = True
        
        # Store user contexts
        self.user_context = {}
        
        # Default interval in seconds
        self.default_interval = 300
        
        # Preset intervals in minutes
        self.preset_intervals = {
            '0.5 min': 30,
            '1 min': 60,
            '2 min': 120,
            '5 min': 300,
            '10 min': 600,
            '15 min': 900,
            '30 min': 1800,
            '60 min': 3600
        }
        
        # User statistics with names and expiry
        self.user_stats = {}
        
        # File to store authorized users
        self.user_file = "authorized_users.json"
        self.load_users()
        
        # Start expiry checker thread
        self.expiry_checker_thread = Thread(target=self.check_expired_users, daemon=True)
        self.expiry_checker_thread.start()
    
    def load_users(self):
        """Load authorized users from file"""
        global AUTHORIZED_USERS
        try:
            with open(self.user_file, 'r') as f:
                data = json.load(f)
                AUTHORIZED_USERS = data.get('users', [])
                self.user_stats = data.get('stats', {})
                logger.info(f"✅ Loaded {len(AUTHORIZED_USERS)} authorized users from file")
                self._clean_expired_users()
        except FileNotFoundError:
            logger.info("📝 No user file found, starting fresh")
            self.save_users()
        except Exception as e:
            logger.error(f"❌ Error loading users: {e}")
    
    def save_users(self):
        """Save authorized users to file"""
        try:
            data = {
                'users': AUTHORIZED_USERS,
                'stats': self.user_stats
            }
            with open(self.user_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"💾 Saved {len(AUTHORIZED_USERS)} authorized users to file")
        except Exception as e:
            logger.error(f"❌ Error saving users: {e}")
    
    def _clean_expired_users(self):
        """Remove expired users from list"""
        global AUTHORIZED_USERS
        expired_users = []
        
        for user_id in AUTHORIZED_USERS[:]:
            if user_id in self.user_stats:
                expiry = self.user_stats[user_id].get('expiry_date')
                if expiry:
                    try:
                        expiry_date = datetime.fromisoformat(expiry)
                        if datetime.now() > expiry_date:
                            expired_users.append(user_id)
                            AUTHORIZED_USERS.remove(user_id)
                            logger.info(f"⏰ Removed expired user: {user_id}")
                    except:
                        pass
        
        if expired_users:
            self.save_users()
    
    def check_expired_users(self):
        """Background thread to check for expired users"""
        while self.running:
            time.sleep(60)
            self._clean_expired_users()
    
    def get_user_name(self, user_id):
        """Get user name from stats or return ID"""
        user_id = str(user_id)
        if user_id in self.user_stats:
            name = self.user_stats[user_id].get('name', '')
            if name:
                return name
        return user_id
    
    def update_user_name(self, user_id, username, first_name, last_name=""):
        """Update user name in stats"""
        user_id = str(user_id)
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'first_seen': datetime.now().isoformat(),
                'total_checks': 0,
                'monitors_started': 0
            }
        
        name = first_name if first_name else ""
        if last_name:
            name += " " + last_name
        if username:
            name += f" (@{username})"
        
        if not name.strip():
            name = user_id
        
        self.user_stats[user_id]['name'] = name
        self.user_stats[user_id]['last_seen'] = datetime.now().isoformat()
        self.save_users()
        
        return name
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return str(user_id) in ADMIN_USERS
    
    def is_authorized(self, user_id):
        """Check if user is authorized and not expired"""
        user_id = str(user_id)
        
        if user_id in ADMIN_USERS:
            return True
        
        if ALLOW_ALL_USERS:
            return True
        
        if user_id not in AUTHORIZED_USERS:
            return False
        
        if user_id in self.user_stats:
            expiry = self.user_stats[user_id].get('expiry_date')
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_date:
                        if user_id in AUTHORIZED_USERS:
                            AUTHORIZED_USERS.remove(user_id)
                            self.save_users()
                        return False
                except:
                    pass
        
        return True
    
    def parse_duration(self, duration_str):
        """Parse duration string like '1h', '2d', '3m', '4w', '5M', '1y'"""
        duration_str = duration_str.strip().lower()
        
        match = re.match(r'^(\d+)\s*([hdwmMy]?)$', duration_str)
        if not match:
            return None
        
        value = int(match.group(1))
        unit = match.group(2) if match.group(2) else 'd'
        
        if unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        elif unit == 'M':
            return timedelta(days=value * 30)
        elif unit == 'y':
            return timedelta(days=value * 365)
        else:
            return timedelta(days=value)
    
    def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """Send a message to Telegram with optional keyboard"""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None

    def send_typing(self, chat_id):
        """Send typing indicator"""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
            data = {'chat_id': chat_id, 'action': 'typing'}
            requests.post(url, data=data, timeout=5)
        except:
            pass

    def format_time(self, seconds):
        """Format seconds into minutes and seconds"""
        if seconds >= 60:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds == 0:
                return f"{minutes} min"
            return f"{minutes} min {remaining_seconds}s"
        return f"{seconds}s"

    def get_main_menu(self, user_id):
        """Create main menu keyboard with admin options if admin"""
        keyboard = [
            ['📱 Check All Stock', '🎨 Check Color'],
            ['🏪 Check Store', '🔔 Monitor'],
            ['⏹️ Stop Monitor', '📊 Status'],
            ['ℹ️ Help']
        ]
        
        if self.is_admin(user_id):
            keyboard.append(['👑 Admin Panel'])
        
        return {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def get_admin_menu(self):
        """Create admin menu keyboard"""
        return {
            'keyboard': [
                ['➕ Add User', '➖ Remove User'],
                ['📋 List Users', '📊 User Stats'],
                ['🔓 Open Mode', '🔒 Restricted Mode'],
                ['🔙 Back to Menu']
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def get_add_user_menu(self):
        """Create add user duration menu"""
        return {
            'keyboard': [
                ['1h', '6h', '12h'],
                ['1d', '3d', '7d'],
                ['15d', '30d', '60d'],
                ['90d', '180d', '365d'],
                ['🔄 Permanent', '🔙 Back to Menu']
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def get_monitor_menu(self):
        """Create monitor menu keyboard"""
        return {
            'keyboard': [
                ['🎨 Specific Color @ All Stores'],
                ['🌈 All Colors @ All Stores'],
                ['🏪 All Colors @ One Store'],
                ['⏱️ Change Monitor Time'],
                ['🔙 Back to Menu']
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def get_color_menu(self):
        """Create color selection keyboard"""
        return {
            'keyboard': [
                ['🟣 Lavender', '🟢 Sage'],
                ['🔵 Mist Blue', '⚪ White'],
                ['⚫ Black'],
                ['🔙 Back to Menu']
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def get_store_menu(self):
        """Create store selection keyboard"""
        return {
            'keyboard': [
                ['Saket', 'Noida', 'BKC'],
                ['Borivali', 'Hebbal', 'Koregaon Park'],
                ['🔙 Back to Menu']
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def get_interval_menu(self):
        """Create time interval selection keyboard in minutes"""
        return {
            'keyboard': [
                ['0.5 min', '1 min', '2 min'],
                ['5 min', '10 min', '15 min'],
                ['30 min', '60 min'],
                ['✏️ Custom Time', '🔙 Back to Menu']
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }

    def format_stock_report(self, available):
        """Format stock report for Telegram"""
        if not available:
            return "❌ No iPhone 17 256GB models available at any store!\n\n🕐 " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = []
        lines.append("📱 *iPhone 17 256GB - Stock Report*")
        lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("─" * 30)
        lines.append("")
        
        by_color = {}
        for item in available:
            color = item['color']
            if color not in by_color:
                by_color[color] = []
            by_color[color].append(item)
        
        for color, items in by_color.items():
            emoji = self.checker.colors[color]['emoji']
            lines.append(f"*{emoji} {color}*")
            for item in items:
                pickup = item.get('pickup_date', 'Available')
                if pickup == 'Available' or not pickup:
                    pickup = 'Available Now'
                lines.append(f"  ✅ {item['store']} ({item['city']})")
                lines.append(f"     📅 Pickup: {pickup}")
            lines.append("")
        
        lines.append("─" * 30)
        lines.append(f"✅ Total: {len(available)} combinations")
        
        return "\n".join(lines)

    def format_help(self, user_id):
        """Format help message with admin info if admin"""
        help_text = """
🤖 *Apple Stock Bot - Easy Commands*

*Simple Commands:*
📱 Check All Stock - Check everywhere
🎨 Check Color - Pick a color to check
🏪 Check Store - Pick a store to check

🔔 *Monitor Commands:*
🎨 Specific Color @ All Stores - Monitor one color everywhere
🌈 All Colors @ All Stores - Monitor all colors everywhere
🏪 All Colors @ One Store - Monitor all colors at one store
⏱️ Change Monitor Time - Change check interval (in MINUTES)

⏹️ Stop Monitor - Stop all alerts
📊 Status - Check if bot is working
ℹ️ Help - Show this message
"""
        
        if self.is_admin(user_id):
            help_text += """

👑 *Admin Commands:*
/adduser <user_id> <duration> - Add user with expiry
  Duration format: 1h, 1d, 1w, 1M, 1y
  Example: /adduser 123456789 7d (7 days access)
  Or: /adduser 123456789 permanent

/removeuser <user_id> - Remove user
/listusers - List all authorized users
/userstats - Show user statistics
/openmode - Allow all users
/restrictedmode - Restrict to authorized users
"""
        
        return help_text

    def handle_start(self, chat_id):
        """Handle /start command"""
        if chat_id not in self.user_stats:
            self.user_stats[chat_id] = {
                'first_seen': datetime.now().isoformat(),
                'total_checks': 0,
                'monitors_started': 0
            }
        
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
            params = {'chat_id': chat_id}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    user_data = data.get('result', {})
                    first_name = user_data.get('first_name', '')
                    last_name = user_data.get('last_name', '')
                    username = user_data.get('username', '')
                    self.update_user_name(chat_id, username, first_name, last_name)
        except:
            pass
        
        if not self.is_authorized(chat_id):
            if chat_id in self.user_stats:
                expiry = self.user_stats[chat_id].get('expiry_date')
                if expiry:
                    try:
                        expiry_date = datetime.fromisoformat(expiry)
                        if datetime.now() > expiry_date:
                            self.send_message(chat_id, 
                                "⏰ *Access Expired!*\n\n"
                                "Your access to Apple Stock Bot has expired.\n"
                                f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                "Please contact the admin to renew your access.",
                                parse_mode="Markdown"
                            )
                            return
                    except:
                        pass
            
            self.send_message(chat_id, 
                "⛔ *Access Denied!*\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the bot administrator to get access.\n\n"
                "💡 If you're an admin, use:\n"
                "/adduser <user_id> <duration> to add users\n"
                "/openmode to allow all users",
                parse_mode="Markdown"
            )
            return
        
        expiry_text = "Permanent"
        if chat_id in self.user_stats:
            expiry = self.user_stats[chat_id].get('expiry_date')
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_date:
                        expiry_text = "⏰ EXPIRED"
                    else:
                        expiry_text = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        message = f"""
👋 *Welcome to Apple Stock Bot!*

I check iPhone 17 256GB availability at Apple Stores in India.

📅 *Your Access Details:*
• Status: {'✅ Active' if self.is_authorized(chat_id) else '❌ Inactive'}
• Expiry: {expiry_text}

*Just use the buttons below:* 👇

📱 *Check All Stock* - See everything available
🎨 *Check Color* - Check a specific color
🏪 *Check Store* - Check a specific store

🔔 *Monitor Commands:*
• Monitor a color at ALL stores
• Monitor ALL colors at ALL stores
• Monitor ALL colors at ONE store
• Change check interval (in MINUTES)

Type /help anytime for help!
"""
        self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_main_menu(chat_id))

    def handle_help(self, chat_id):
        """Handle /help command"""
        if not self.is_authorized(chat_id):
            return
        
        self.send_message(chat_id, self.format_help(chat_id), parse_mode="Markdown", reply_markup=self.get_main_menu(chat_id))

    def handle_check_all(self, chat_id):
        """Handle check all stock"""
        if not self.is_authorized(chat_id):
            return
        
        try:
            self.send_typing(chat_id)
            self.send_message(chat_id, "🔍 Checking all stores... ⏳")
            
            available = self.checker.check_all_stores_all_colors()
            report = self.format_stock_report(available)
            self.send_message(chat_id, report, parse_mode="Markdown", reply_markup=self.get_main_menu(chat_id))
            
            if chat_id in self.user_stats:
                self.user_stats[chat_id]['total_checks'] = self.user_stats[chat_id].get('total_checks', 0) + 1
                self.save_users()
            
        except Exception as e:
            self.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=self.get_main_menu(chat_id))

    def handle_color_selection(self, chat_id, color_name):
        """Handle color selection from menu"""
        if not self.is_authorized(chat_id):
            return
        
        try:
            self.send_typing(chat_id)
            self.send_message(chat_id, f"🔍 Checking {color_name}... ⏳")
            
            result = self.checker.check_color_all_stores(color_name)
            
            if result is None:
                self.send_message(chat_id, f"❌ Color '{color_name}' not found!", reply_markup=self.get_color_menu())
                return
            
            if result:
                message = f"✅ *{color_name}* available at:\n\n"
                for item in result:
                    pickup = item.get('pickup_date', 'Available')
                    if pickup == 'Available' or not pickup:
                        pickup = 'Available Now'
                    message += f"  📍 {item['store']} ({item['city']})\n"
                    message += f"     📅 Pickup: {pickup}\n\n"
                self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_main_menu(chat_id))
            else:
                self.send_message(chat_id, f"❌ {color_name} is out of stock everywhere!", reply_markup=self.get_main_menu(chat_id))
            
            if chat_id in self.user_stats:
                self.user_stats[chat_id]['total_checks'] = self.user_stats[chat_id].get('total_checks', 0) + 1
                self.save_users()
                
        except Exception as e:
            self.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=self.get_main_menu(chat_id))

    def handle_store_selection(self, chat_id, store_name):
        """Handle store selection from menu"""
        if not self.is_authorized(chat_id):
            return
        
        try:
            self.send_typing(chat_id)
            self.send_message(chat_id, f"🔍 Checking {store_name}... ⏳")
            
            result = self.checker.check_all_colors_specific_store(store_name)
            
            if result is None:
                self.send_message(chat_id, f"❌ Store '{store_name}' not found!", reply_markup=self.get_store_menu())
                return
            
            if result:
                message = f"✅ *Available at {store_name}:*\n\n"
                for item in result:
                    emoji = self.checker.colors[item['color']]['emoji']
                    pickup = item.get('pickup_date', 'Available')
                    if pickup == 'Available' or not pickup:
                        pickup = 'Available Now'
                    message += f"  {emoji} {item['color']} - Pickup: {pickup}\n"
                self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_main_menu(chat_id))
            else:
                self.send_message(chat_id, f"❌ No iPhone 17 256GB available at {store_name}!", reply_markup=self.get_main_menu(chat_id))
            
            if chat_id in self.user_stats:
                self.user_stats[chat_id]['total_checks'] = self.user_stats[chat_id].get('total_checks', 0) + 1
                self.save_users()
                
        except Exception as e:
            self.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=self.get_main_menu(chat_id))

    def handle_stop_monitor(self, chat_id):
        """Handle stop monitor for a user"""
        if not self.is_authorized(chat_id):
            return
        
        user_monitors = self.get_user_monitors(chat_id)
        
        with self.monitoring_lock:
            if not user_monitors:
                self.send_message(chat_id, "⚠️ No active monitors!", reply_markup=self.get_main_menu(chat_id))
                return
            
            count = len(user_monitors)
            user_monitors.clear()
            self.send_message(chat_id, f"✅ Stopped {count} monitor(s)", reply_markup=self.get_main_menu(chat_id))

    def handle_status(self, chat_id):
        """Handle status check for a user"""
        if not self.is_authorized(chat_id):
            return
        
        try:
            self.send_typing(chat_id)
            status = self.checker.test_api_status()
            
            user_monitors = self.get_user_monitors(chat_id)
            active_monitors = len(user_monitors)
            
            current_interval = self.user_context.get(chat_id, {}).get('new_interval', self.default_interval)
            time_display = self.format_time(current_interval)
            
            stats = self.user_stats.get(chat_id, {})
            total_checks = stats.get('total_checks', 0)
            
            expiry_text = "Permanent"
            expiry = stats.get('expiry_date')
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_date:
                        expiry_text = "⏰ EXPIRED"
                    else:
                        expiry_text = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            if status.get('working'):
                message = (
                    f"✅ *Bot Status*\n\n"
                    f"API: Working ✅\n"
                    f"Response: {status['response_time']}s\n"
                    f"Active Monitors: {active_monitors}\n"
                    f"Current Interval: {time_display}\n"
                    f"Total Checks: {total_checks}\n"
                    f"Access Expiry: {expiry_text}\n\n"
                    f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                message = (
                    f"❌ *Bot Status*\n\n"
                    f"API: Error ❌\n"
                    f"Error: {status.get('error', 'Unknown')}\n"
                    f"Active Monitors: {active_monitors}\n"
                    f"Current Interval: {time_display}"
                )
            self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_main_menu(chat_id))
        except Exception as e:
            self.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=self.get_main_menu(chat_id))

    def handle_change_interval(self, chat_id):
        """Handle change monitoring interval for a user"""
        if not self.is_authorized(chat_id):
            return
        
        current_interval = self.user_context.get(chat_id, {}).get('new_interval', self.default_interval)
        time_display = self.format_time(current_interval)
        
        if chat_id not in self.user_context:
            self.user_context[chat_id] = {}
        self.user_context[chat_id]['changing_interval'] = True
        
        self.send_message(chat_id, 
            f"⏱️ *Change Monitor Time*\n\n"
            f"Current: {time_display}\n\n"
            f"Select preset time below OR type any number in MINUTES:\n"
            f"• Type: 3 (for 3 minutes)\n"
            f"• Type: 7.5 (for 7.5 minutes)\n"
            f"• Type: 20 (for 20 minutes)\n\n"
            f"⏱️ Minimum: 0.5 min | Maximum: 60 min",
            parse_mode="Markdown",
            reply_markup=self.get_interval_menu()
        )

    def handle_set_interval(self, chat_id, time_input):
        """Handle setting new interval from preset or custom input"""
        if not self.is_authorized(chat_id):
            return
        
        try:
            if time_input in self.preset_intervals:
                new_interval = self.preset_intervals[time_input]
            else:
                parsed = self.parse_time_input(time_input)
                if parsed is None:
                    self.send_message(chat_id, 
                        "❌ Invalid time! Please enter a number in MINUTES.\n"
                        "Example: 3, 7.5, 15, 30\n\n"
                        "Or use the preset buttons.",
                        reply_markup=self.get_interval_menu()
                    )
                    return
                new_interval = parsed
            
            if chat_id not in self.user_context:
                self.user_context[chat_id] = {}
            self.user_context[chat_id]['new_interval'] = new_interval
            time_display = self.format_time(new_interval)
            
            user_monitors = self.get_user_monitors(chat_id)
            
            self.send_message(chat_id,
                f"✅ *Interval Updated!*\n\n"
                f"⏱️ New check interval: {time_display}\n\n"
                f"💡 This will apply to NEW monitors only.\n"
                f"To change existing monitors, stop and restart them.\n\n"
                f"Current active monitors: {len(user_monitors)}\n\n"
                f"📌 Start a monitor from the Monitor menu!",
                parse_mode="Markdown",
                reply_markup=self.get_main_menu(chat_id)
            )
            
            self.user_context[chat_id]['changing_interval'] = False
            
        except Exception as e:
            self.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=self.get_main_menu(chat_id))

    def get_user_monitors(self, chat_id):
        """Get all monitors for a user"""
        if chat_id not in self.monitoring_threads:
            self.monitoring_threads[chat_id] = {}
        return self.monitoring_threads[chat_id]

    def parse_time_input(self, text):
        """Parse time input from user (supports minutes)"""
        try:
            minutes = float(text)
            if minutes <= 0:
                return None
            seconds = int(minutes * 60)
            if seconds < 30:
                return 30
            if seconds > 3600:
                return 3600
            return seconds
        except ValueError:
            return None

    def monitor_specific_color_all_stores(self, chat_id, color_name, interval=300):
        """Monitor a single color at all stores"""
        monitor_key = f"allstores_{color_name}"
        user_monitors = self.get_user_monitors(chat_id)
        
        with self.monitoring_lock:
            if monitor_key in user_monitors:
                self.send_message(chat_id, f"⚠️ Already monitoring {color_name} at all stores!", reply_markup=self.get_main_menu(chat_id))
                return
            
            thread = Thread(
                target=self.monitor_all_stores_loop,
                args=(chat_id, color_name, interval, monitor_key),
                daemon=True
            )
            user_monitors[monitor_key] = thread
            thread.start()
        
        time_display = self.format_time(interval)
        self.send_message(chat_id,
            f"✅ *Monitoring Started!*\n\n"
            f"📱 Color: {color_name}\n"
            f"🏪 Stores: ALL STORES\n"
            f"⏱️ Checking every: {time_display}\n\n"
            f"🔔 You'll be notified when {color_name} is available ANYWHERE!\n"
            f"Use ⏹️ Stop Monitor to stop.",
            parse_mode="Markdown",
            reply_markup=self.get_main_menu(chat_id)
        )

    def monitor_all_colors_all_stores(self, chat_id, interval=300):
        """Monitor all colors at all stores"""
        monitor_key = "allcolors_allstores"
        user_monitors = self.get_user_monitors(chat_id)
        
        with self.monitoring_lock:
            if monitor_key in user_monitors:
                self.send_message(chat_id, f"⚠️ Already monitoring ALL colors at ALL stores!", reply_markup=self.get_main_menu(chat_id))
                return
            
            thread = Thread(
                target=self.monitor_all_colors_all_stores_loop,
                args=(chat_id, interval, monitor_key),
                daemon=True
            )
            user_monitors[monitor_key] = thread
            thread.start()
        
        time_display = self.format_time(interval)
        self.send_message(chat_id,
            f"✅ *Monitoring Started!*\n\n"
            f"🌈 Colors: ALL COLORS\n"
            f"🏪 Stores: ALL STORES\n"
            f"⏱️ Checking every: {time_display}\n\n"
            f"🔔 You'll be notified when ANY color is available ANYWHERE!\n"
            f"Use ⏹️ Stop Monitor to stop.",
            parse_mode="Markdown",
            reply_markup=self.get_main_menu(chat_id)
        )

    def monitor_all_colors_one_store(self, chat_id, store_name, interval=300):
        """Monitor all colors at one specific store"""
        monitor_key = f"allcolors_{store_name}"
        user_monitors = self.get_user_monitors(chat_id)
        
        with self.monitoring_lock:
            if monitor_key in user_monitors:
                self.send_message(chat_id, f"⚠️ Already monitoring ALL colors at {store_name}!", reply_markup=self.get_main_menu(chat_id))
                return
            
            thread = Thread(
                target=self.monitor_all_colors_one_store_loop,
                args=(chat_id, store_name, interval, monitor_key),
                daemon=True
            )
            user_monitors[monitor_key] = thread
            thread.start()
        
        store_info = self.checker.stores[store_name]
        time_display = self.format_time(interval)
        self.send_message(chat_id,
            f"✅ *Monitoring Started!*\n\n"
            f"🌈 Colors: ALL COLORS\n"
            f"🏪 Store: {store_name} ({store_info['city']})\n"
            f"⏱️ Checking every: {time_display}\n\n"
            f"🔔 You'll be notified when ANY color is available at {store_name}!\n"
            f"Use ⏹️ Stop Monitor to stop.",
            parse_mode="Markdown",
            reply_markup=self.get_main_menu(chat_id)
        )

    def monitor_all_stores_loop(self, chat_id, color_name, interval, monitor_key):
        """Monitor a single color at all stores"""
        color_info = self.checker.colors[color_name]
        previous_status = {}
        
        for store_name in self.checker.stores.keys():
            previous_status[store_name] = False
        
        while self.running and monitor_key in self.get_user_monitors(chat_id):
            try:
                for store_name, store_info in self.checker.stores.items():
                    result = self.checker.check_product(
                        color_info['sku'],
                        store_info['code']
                    )
                    
                    current_status = result.get('in_stock', False)
                    
                    if current_status and not previous_status.get(store_name, False):
                        pickup = result.get('pickup_date', 'Available')
                        if pickup == 'Available' or not pickup:
                            pickup = 'Available Now'
                        
                        message = (
                            f"🔔 *STOCK ALERT!*\n\n"
                            f"✅ *{color_name}* is now IN STOCK!\n"
                            f"📍 {store_name} ({store_info['city']})\n"
                            f"📅 Pickup: {pickup}\n\n"
                            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"💡 Hurry! Stock may not last long!"
                        )
                        self.send_message(chat_id, message, parse_mode="Markdown")
                        previous_status[store_name] = True
                    
                    elif not current_status and previous_status.get(store_name, False):
                        message = (
                            f"🔔 *STOCK UPDATE*\n\n"
                            f"❌ *{color_name}* is now OUT OF STOCK\n"
                            f"📍 {store_name} ({store_info['city']})\n\n"
                            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        self.send_message(chat_id, message, parse_mode="Markdown")
                        previous_status[store_name] = False
                    
                    time.sleep(0.3)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitor error for user {chat_id}: {e}")
                time.sleep(interval)
        
        with self.monitoring_lock:
            user_monitors = self.monitoring_threads.get(chat_id, {})
            if monitor_key in user_monitors:
                del user_monitors[chat_id][monitor_key]

    def monitor_all_colors_all_stores_loop(self, chat_id, interval, monitor_key):
        """Monitor all colors at all stores"""
        previous_status = {}
        for color_name in self.checker.colors.keys():
            for store_name in self.checker.stores.keys():
                key = f"{color_name}_{store_name}"
                previous_status[key] = False
        
        while self.running and monitor_key in self.get_user_monitors(chat_id):
            try:
                for color_name, color_info in self.checker.colors.items():
                    for store_name, store_info in self.checker.stores.items():
                        result = self.checker.check_product(
                            color_info['sku'],
                            store_info['code']
                        )
                        
                        current_status = result.get('in_stock', False)
                        key = f"{color_name}_{store_name}"
                        
                        if current_status and not previous_status.get(key, False):
                            pickup = result.get('pickup_date', 'Available')
                            if pickup == 'Available' or not pickup:
                                pickup = 'Available Now'
                            emoji = self.checker.colors[color_name]['emoji']
                            
                            message = (
                                f"🔔 *STOCK ALERT!*\n\n"
                                f"{emoji} *{color_name}* is now IN STOCK!\n"
                                f"📍 {store_name} ({store_info['city']})\n"
                                f"📅 Pickup: {pickup}\n\n"
                                f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                f"💡 Hurry! Stock may not last long!"
                            )
                            self.send_message(chat_id, message, parse_mode="Markdown")
                            previous_status[key] = True
                        
                        elif not current_status and previous_status.get(key, False):
                            emoji = self.checker.colors[color_name]['emoji']
                            message = (
                                f"🔔 *STOCK UPDATE*\n\n"
                                f"{emoji} *{color_name}* is now OUT OF STOCK\n"
                                f"📍 {store_name} ({store_info['city']})\n\n"
                                f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            self.send_message(chat_id, message, parse_mode="Markdown")
                            previous_status[key] = False
                        
                        time.sleep(0.2)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitor error for user {chat_id}: {e}")
                time.sleep(interval)
        
        with self.monitoring_lock:
            user_monitors = self.monitoring_threads.get(chat_id, {})
            if monitor_key in user_monitors:
                del user_monitors[chat_id][monitor_key]

    def monitor_all_colors_one_store_loop(self, chat_id, store_name, interval, monitor_key):
        """Monitor all colors at one specific store"""
        store_info = self.checker.stores[store_name]
        previous_status = {}
        
        for color_name in self.checker.colors.keys():
            previous_status[color_name] = False
        
        while self.running and monitor_key in self.get_user_monitors(chat_id):
            try:
                for color_name, color_info in self.checker.colors.items():
                    result = self.checker.check_product(
                        color_info['sku'],
                        store_info['code']
                    )
                    
                    current_status = result.get('in_stock', False)
                    
                    if current_status and not previous_status.get(color_name, False):
                        pickup = result.get('pickup_date', 'Available')
                        if pickup == 'Available' or not pickup:
                            pickup = 'Available Now'
                        emoji = self.checker.colors[color_name]['emoji']
                        
                        message = (
                            f"🔔 *STOCK ALERT!*\n\n"
                            f"{emoji} *{color_name}* is now IN STOCK!\n"
                            f"📍 {store_name} ({store_info['city']})\n"
                            f"📅 Pickup: {pickup}\n\n"
                            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"💡 Hurry! Stock may not last long!"
                        )
                        self.send_message(chat_id, message, parse_mode="Markdown")
                        previous_status[color_name] = True
                    
                    elif not current_status and previous_status.get(color_name, False):
                        emoji = self.checker.colors[color_name]['emoji']
                        message = (
                            f"🔔 *STOCK UPDATE*\n\n"
                            f"{emoji} *{color_name}* is now OUT OF STOCK\n"
                            f"📍 {store_name} ({store_info['city']})\n\n"
                            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        self.send_message(chat_id, message, parse_mode="Markdown")
                        previous_status[color_name] = False
                    
                    time.sleep(0.2)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitor error for user {chat_id}: {e}")
                time.sleep(interval)
        
        with self.monitoring_lock:
            user_monitors = self.monitoring_threads.get(chat_id, {})
            if monitor_key in user_monitors:
                del user_monitors[chat_id][monitor_key]

    def handle_add_user_with_duration(self, chat_id, user_id, duration):
        """Add user with duration"""
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        user_id = user_id.strip()
        duration = duration.strip().lower()
        
        if not user_id.isdigit():
            self.send_message(chat_id, "❌ Invalid user ID! Must be numeric.", reply_markup=self.get_admin_menu())
            return
        
        if user_id in AUTHORIZED_USERS:
            name = self.get_user_name(user_id)
            self.send_message(chat_id, f"⚠️ User {name} is already authorized!", reply_markup=self.get_admin_menu())
            return
        
        if user_id in ADMIN_USERS:
            self.send_message(chat_id, f"⚠️ User {user_id} is an admin! They already have access.", reply_markup=self.get_admin_menu())
            return
        
        expiry_date = None
        expiry_display = "Permanent"
        
        if duration != 'permanent':
            delta = self.parse_duration(duration)
            if delta is None:
                self.send_message(chat_id, 
                    "❌ Invalid duration format!\n\n"
                    "Valid formats:\n"
                    "• 1h, 6h, 12h - Hours\n"
                    "• 1d, 3d, 7d - Days\n"
                    "• 15d, 30d, 60d - Days\n"
                    "• 90d, 180d, 365d - Days\n"
                    "• permanent - No expiry\n\n"
                    "Example: /adduser 123456789 7d",
                    reply_markup=self.get_admin_menu()
                )
                return
            
            expiry_date = datetime.now() + delta
            expiry_display = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
        name = user_id
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
            params = {'chat_id': user_id}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    user_data = data.get('result', {})
                    first_name = user_data.get('first_name', '')
                    last_name = user_data.get('last_name', '')
                    username = user_data.get('username', '')
                    name = first_name if first_name else user_id
                    if last_name:
                        name += " " + last_name
                    if username:
                        name += f" (@{username})"
        except:
            pass
        
        AUTHORIZED_USERS.append(user_id)
        
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'first_seen': datetime.now().isoformat(),
                'total_checks': 0,
                'monitors_started': 0
            }
        
        self.user_stats[user_id]['name'] = name
        self.user_stats[user_id]['added_by'] = chat_id
        self.user_stats[user_id]['added_date'] = datetime.now().isoformat()
        if expiry_date:
            self.user_stats[user_id]['expiry_date'] = expiry_date.isoformat()
        else:
            self.user_stats[user_id]['expiry_date'] = None
        
        self.save_users()
        
        expiry_text = "Permanent" if not expiry_date else expiry_display
        self.send_message(chat_id, 
            f"✅ *User Added Successfully!*\n\n"
            f"👤 Name: {name}\n"
            f"🆔 ID: `{user_id}`\n"
            f"⏰ Expiry: {expiry_text}\n\n"
            f"They can now use the bot.\n"
            f"Tell them to send /start to get started.",
            parse_mode="Markdown",
            reply_markup=self.get_admin_menu()
        )
        
        try:
            welcome_msg = (
                "🎉 *You've been granted access to Apple Stock Bot!*\n\n"
                f"📅 Access Expiry: {expiry_text}\n\n"
                "Send /start to begin using the bot.\n"
                "You can check iPhone 17 256GB availability at Apple Stores."
            )
            self.send_message(user_id, welcome_msg, parse_mode="Markdown", reply_markup=self.get_main_menu(user_id))
        except:
            pass

    def handle_remove_user(self, chat_id, args):
        """Remove a user"""
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        if not args:
            self.send_message(chat_id, 
                "❌ Please provide a user ID!\n\n"
                "Example: /removeuser 123456789",
                reply_markup=self.get_admin_menu()
            )
            return
        
        user_id = args[0].strip()
        user_name = self.get_user_name(user_id)
        
        if user_id not in AUTHORIZED_USERS:
            self.send_message(chat_id, f"⚠️ User {user_name} is not in the authorized list!", reply_markup=self.get_admin_menu())
            return
        
        if user_id in ADMIN_USERS:
            self.send_message(chat_id, f"⚠️ User {user_name} is an admin! Admins cannot be removed.", reply_markup=self.get_admin_menu())
            return
        
        AUTHORIZED_USERS.remove(user_id)
        self.save_users()
        
        if user_id in self.monitoring_threads:
            self.monitoring_threads[user_id].clear()
        
        self.send_message(chat_id, 
            f"✅ User *{user_name}* (`{user_id}`) has been removed!\n\n"
            f"They can no longer use the bot.",
            parse_mode="Markdown",
            reply_markup=self.get_admin_menu()
        )
        
        try:
            self.send_message(user_id, 
                "❌ *Access Revoked!*\n\n"
                "Your access to Apple Stock Bot has been removed.\n"
                "Contact the admin if you think this is a mistake.",
                parse_mode="Markdown"
            )
        except:
            pass

    def handle_list_users(self, chat_id):
        """List all authorized users with names, joining date, and expiry"""
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        if not AUTHORIZED_USERS:
            self.send_message(chat_id, "📋 No authorized users.", reply_markup=self.get_admin_menu())
            return
        
        message = "📋 *Authorized Users:*\n\n"
        message += "│ # │ User Name │ ID │ Joined │ Expiry │ Monitors │\n"
        message += "│───│───────────│────│────────│────────│──────────│\n"
        
        for i, user_id in enumerate(AUTHORIZED_USERS, 1):
            user_name = self.get_user_name(user_id)
            
            stats = self.user_stats.get(user_id, {})
            joined_date = stats.get('first_seen', 'N/A')
            if joined_date != 'N/A':
                try:
                    joined = datetime.fromisoformat(joined_date)
                    joined_date = joined.strftime('%Y-%m-%d')
                except:
                    joined_date = 'N/A'
            
            expiry = stats.get('expiry_date')
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_date:
                        expiry_display = "⏰ EXPIRED"
                    else:
                        expiry_display = expiry_date.strftime('%Y-%m-%d')
                except:
                    expiry_display = 'N/A'
            else:
                expiry_display = '🔄 Permanent'
            
            monitors = len(self.monitoring_threads.get(user_id, {}))
            
            display_name = user_name
            if len(display_name) > 20:
                display_name = display_name[:17] + "..."
            
            message += f"│ {i:2} │ {display_name:<20} │ `{user_id}` │ {joined_date} │ {expiry_display} │ {monitors:8} │\n"
        
        message += f"\n*Total: {len(AUTHORIZED_USERS)} users*"
        
        self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_admin_menu())

    def handle_user_stats(self, chat_id):
        """Show user statistics with names and joining dates"""
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        if not self.user_stats:
            self.send_message(chat_id, "📊 No user statistics available yet.", reply_markup=self.get_admin_menu())
            return
        
        message = "📊 *User Statistics*\n\n"
        message += "│ # │ User Name │ ID │ Joined │ Checks │ Monitors │ Status │\n"
        message += "│───│───────────│────│────────│────────│──────────│────────│\n"
        
        sorted_users = sorted(self.user_stats.items(), key=lambda x: x[1].get('total_checks', 0), reverse=True)
        
        for i, (user_id, stats) in enumerate(sorted_users[:25], 1):
            user_name = stats.get('name', user_id)
            if len(user_name) > 18:
                user_name = user_name[:15] + "..."
            
            joined_date = stats.get('first_seen', 'N/A')
            if joined_date != 'N/A':
                try:
                    joined = datetime.fromisoformat(joined_date)
                    joined_date = joined.strftime('%Y-%m-%d')
                except:
                    joined_date = 'N/A'
            
            total_checks = stats.get('total_checks', 0)
            active_monitors = len(self.monitoring_threads.get(user_id, {}))
            
            if user_id in ADMIN_USERS:
                status = "👑 Admin"
            elif user_id in AUTHORIZED_USERS:
                expiry = stats.get('expiry_date')
                if expiry:
                    try:
                        expiry_date = datetime.fromisoformat(expiry)
                        if datetime.now() > expiry_date:
                            status = "⏰ Expired"
                        else:
                            status = "✅ Active"
                    except:
                        status = "✅ Active"
                else:
                    status = "✅ Active"
            else:
                status = "❌ Inactive"
            
            message += f"│ {i:2} │ {user_name:<18} │ `{user_id}` │ {joined_date} │ {total_checks:6} │ {active_monitors:8} │ {status:<8} │\n"
        
        total_users = len(self.user_stats)
        total_checks = sum(s.get('total_checks', 0) for s in self.user_stats.values())
        total_monitors = sum(len(self.monitoring_threads.get(uid, {})) for uid in self.user_stats.keys())
        expired_count = 0
        
        for user_id, stats in self.user_stats.items():
            expiry = stats.get('expiry_date')
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_date:
                        expired_count += 1
                except:
                    pass
        
        message += f"\n*Summary:*"
        message += f"\n• Total Users: {total_users}"
        message += f"\n• Active Users: {total_users - expired_count}"
        message += f"\n• Expired Users: {expired_count}"
        message += f"\n• Total Checks: {total_checks}"
        message += f"\n• Total Active Monitors: {total_monitors}"
        
        self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_admin_menu())

    def handle_admin_panel(self, chat_id):
        """Show admin panel"""
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ You are not an admin!", reply_markup=self.get_main_menu(chat_id))
            return
        
        status = "🔓 OPEN" if ALLOW_ALL_USERS else "🔒 RESTRICTED"
        user_count = len(AUTHORIZED_USERS)
        
        total_monitors = 0
        for user_id in self.monitoring_threads:
            total_monitors += len(self.monitoring_threads[user_id])
        
        expired_count = 0
        for user_id in self.user_stats:
            expiry = self.user_stats[user_id].get('expiry_date')
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_date:
                        expired_count += 1
                except:
                    pass
        
        message = f"""
👑 *Admin Panel*

📊 *Current Status:*
• Mode: {status}
• Authorized Users: {user_count}
• Expired Users: {expired_count}
• Total Active Monitors: {total_monitors}

*Available Actions:*
➕ Add User - Give access with expiry
➖ Remove User - Remove user access
📋 List Users - Show all users with expiry
📊 User Stats - Show user statistics
🔓 Open Mode - Allow all users
🔒 Restricted Mode - Only authorized users

*Duration Formats:*
1h, 6h, 12h - Hours
1d, 3d, 7d - Days
15d, 30d, 60d - Days
90d, 180d, 365d - Days
permanent - No expiry

*Commands:*
/adduser <user_id> <duration>
/removeuser <user_id>
/listusers
/userstats
/openmode
/restrictedmode
"""
        self.send_message(chat_id, message, parse_mode="Markdown", reply_markup=self.get_admin_menu())

    def handle_open_mode(self, chat_id):
        """Set bot to open mode (all users can use)"""
        global ALLOW_ALL_USERS
        
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        ALLOW_ALL_USERS = True
        self.send_message(chat_id, 
            "🔓 *Mode Changed to OPEN!*\n\n"
            "Now ALL users can use this bot.\n"
            "No authorization required.\n\n"
            "⚠️ Anyone who finds the bot can use it.",
            parse_mode="Markdown",
            reply_markup=self.get_admin_menu()
        )

    def handle_restricted_mode(self, chat_id):
        """Set bot to restricted mode (only authorized users)"""
        global ALLOW_ALL_USERS
        
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        ALLOW_ALL_USERS = False
        self.send_message(chat_id, 
            "🔒 *Mode Changed to RESTRICTED!*\n\n"
            "Now ONLY authorized users can use this bot.\n"
            "Use /adduser to grant access to new users.\n"
            f"Current authorized users: {len(AUTHORIZED_USERS)}",
            parse_mode="Markdown",
            reply_markup=self.get_admin_menu()
        )

    def handle_add_user_start(self, chat_id, args=None):
        """Start the add user process - ask for duration"""
        if not self.is_admin(chat_id):
            self.send_message(chat_id, "⛔ Admin only command!", reply_markup=self.get_main_menu(chat_id))
            return
        
        if args and len(args) >= 1:
            user_id = args[0]
            duration = args[1] if len(args) >= 2 else None
            
            if duration:
                self.handle_add_user_with_duration(chat_id, user_id, duration)
                return
        
        if args and len(args) >= 1:
            self.user_context[chat_id] = {'adding_user': args[0]}
            self.send_message(chat_id, 
                f"✏️ *Add User - Select Duration*\n\n"
                f"User ID: `{args[0]}`\n\n"
                f"Select access duration below:\n\n"
                f"🕐 *Duration Formats:*\n"
                f"• 1h, 6h, 12h - Hours\n"
                f"• 1d, 3d, 7d - Days\n"
                f"• 15d, 30d, 60d - Days\n"
                f"• 90d, 180d, 365d - Days\n"
                f"• permanent - No expiry\n\n"
                f"Or type: /adduser {args[0]} <duration>",
                parse_mode="Markdown",
                reply_markup=self.get_add_user_menu()
            )
        else:
            self.send_message(chat_id, 
                "❌ Please provide a user ID!\n\n"
                "Example: /adduser 123456789 7d\n\n"
                "Or press the button and provide user ID.",
                reply_markup=self.get_admin_menu()
            )

    # ============================================
    # MAIN BOT LOOP
    # ============================================

    def run(self):
        """Main bot loop"""
        logger.info("🤖 Starting Telegram Stock Bot...")
        logger.info(f"👥 Multi-User Mode: {'OPEN' if ALLOW_ALL_USERS else 'RESTRICTED'}")
        logger.info(f"👑 Admins: {ADMIN_USERS}")
        logger.info(f"👤 Authorized Users: {len(AUTHORIZED_USERS)}")
        
        try:
            response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                logger.info(f"✅ Bot connected: @{bot_info.get('username')}")
                logger.info(f"🆔 Bot ID: {bot_info.get('id')}")
                
                for admin_id in ADMIN_USERS:
                    self.send_message(admin_id, 
                        "🤖 *Bot Started!*\n\n"
                        f"👥 Mode: {'🔓 OPEN' if ALLOW_ALL_USERS else '🔒 RESTRICTED'}\n"
                        f"👤 Authorized Users: {len(AUTHORIZED_USERS)}\n\n"
                        "Use /admin to open admin panel.\n\n"
                        "📝 Duration Formats:\n"
                        "1h, 6h, 12h - Hours\n"
                        "1d, 3d, 7d - Days\n"
                        "15d, 30d, 60d - Days\n"
                        "90d, 180d, 365d - Days\n"
                        "permanent - No expiry",
                        parse_mode="Markdown",
                        reply_markup=self.get_main_menu(admin_id)
                    )
            else:
                logger.error(f"❌ Failed to connect: {data}")
                return
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return
        
        logger.info("🔄 Listening for messages...")
        
        while self.running:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
                params = {'offset': self.last_update_id + 1, 'timeout': 30}
                response = requests.get(url, params=params, timeout=35)
                data = response.json()
                
                if data.get('ok'):
                    for update in data.get('result', []):
                        self.process_update(update)
                        self.last_update_id = update['update_id']
                else:
                    logger.error(f"API error: {data}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)

    def process_update(self, update):
        """Process a single update"""
        try:
            message = update.get('message')
            if not message:
                return
            
            chat_id = str(message.get('chat', {}).get('id'))
            username = message.get('chat', {}).get('username', 'Unknown')
            first_name = message.get('chat', {}).get('first_name', '')
            last_name = message.get('chat', {}).get('last_name', '')
            
            self.update_user_name(chat_id, username, first_name, last_name)
            
            if not self.is_authorized(chat_id):
                logger.warning(f"⛔ Unauthorized access attempt: {chat_id} (@{username})")
                
                if chat_id in self.user_stats:
                    expiry = self.user_stats[chat_id].get('expiry_date')
                    if expiry:
                        try:
                            expiry_date = datetime.fromisoformat(expiry)
                            if datetime.now() > expiry_date:
                                self.send_message(chat_id, 
                                    "⏰ *Access Expired!*\n\n"
                                    "Your access to Apple Stock Bot has expired.\n"
                                    f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                    "Please contact the admin to renew your access.",
                                    parse_mode="Markdown"
                                )
                                return
                        except:
                            pass
                
                self.send_message(chat_id, 
                    "⛔ *Access Denied!*\n\n"
                    "You are not authorized to use this bot.\n"
                    "Please contact the bot administrator.\n\n"
                    "💡 If you're an admin, use:\n"
                    "/adduser <user_id> <duration> to add users\n"
                    "/openmode to allow all users",
                    parse_mode="Markdown"
                )
                return
            
            text = message.get('text')
            if not text:
                return
            
            logger.info(f"📩 {username} ({chat_id}): {text}")
            
            # ============================================
            # ADMIN COMMANDS
            # ============================================
            
            if text.startswith('/adduser'):
                args = text.split()[1:] if len(text.split()) > 1 else []
                if len(args) >= 2:
                    self.handle_add_user_with_duration(chat_id, args[0], args[1])
                else:
                    self.handle_add_user_start(chat_id, args)
                return
            
            elif text.startswith('/removeuser'):
                args = text.split()[1:] if len(text.split()) > 1 else []
                self.handle_remove_user(chat_id, args)
                return
            
            elif text == '/listusers':
                self.handle_list_users(chat_id)
                return
            
            elif text == '/userstats':
                self.handle_user_stats(chat_id)
                return
            
            elif text == '/openmode':
                self.handle_open_mode(chat_id)
                return
            
            elif text == '/restrictedmode':
                self.handle_restricted_mode(chat_id)
                return
            
            elif text == '/admin':
                self.handle_admin_panel(chat_id)
                return
            
            # ============================================
            # MAIN MENU BUTTONS
            # ============================================
            
            if text == '📱 Check All Stock':
                self.handle_check_all(chat_id)
            
            elif text == '🎨 Check Color':
                self.send_message(chat_id, "🎨 Select a color: 👇", reply_markup=self.get_color_menu())
            
            elif text == '🏪 Check Store':
                self.send_message(chat_id, "🏪 Select a store: 👇", reply_markup=self.get_store_menu())
            
            elif text == '🔔 Monitor':
                self.send_message(chat_id, "🔔 *Monitor Options:*\n\nSelect what you want to monitor 👇", 
                                parse_mode="Markdown", reply_markup=self.get_monitor_menu())
            
            elif text == '⏹️ Stop Monitor':
                self.handle_stop_monitor(chat_id)
            
            elif text == '📊 Status':
                self.handle_status(chat_id)
            
            elif text == 'ℹ️ Help':
                self.handle_help(chat_id)
            
            elif text == '🔙 Back to Menu':
                if chat_id in self.user_context:
                    self.user_context[chat_id] = {}
                self.send_message(chat_id, "📱 Main Menu:", reply_markup=self.get_main_menu(chat_id))
            
            # ============================================
            # ADMIN PANEL BUTTONS
            # ============================================
            
            elif text == '👑 Admin Panel':
                self.handle_admin_panel(chat_id)
            
            elif text == '➕ Add User':
                self.send_message(chat_id, 
                    "✏️ *Add User*\n\n"
                    "Send the user's ID and duration:\n"
                    "/adduser <user_id> <duration>\n\n"
                    "Example: /adduser 123456789 7d\n\n"
                    "📝 Duration Formats:\n"
                    "1h, 6h, 12h - Hours\n"
                    "1d, 3d, 7d - Days\n"
                    "15d, 30d, 60d - Days\n"
                    "90d, 180d, 365d - Days\n"
                    "permanent - No expiry\n\n"
                    "💡 Ask the user to message @userinfobot to get their ID.",
                    parse_mode="Markdown",
                    reply_markup=self.get_admin_menu()
                )
            
            elif text == '➖ Remove User':
                self.send_message(chat_id, 
                    "✏️ *Remove User*\n\n"
                    "Send the user's ID:\n"
                    "/removeuser <user_id>\n\n"
                    "Example: /removeuser 123456789",
                    parse_mode="Markdown",
                    reply_markup=self.get_admin_menu()
                )
            
            elif text == '📋 List Users':
                self.handle_list_users(chat_id)
            
            elif text == '📊 User Stats':
                self.handle_user_stats(chat_id)
            
            elif text == '🔓 Open Mode':
                self.handle_open_mode(chat_id)
            
            elif text == '🔒 Restricted Mode':
                self.handle_restricted_mode(chat_id)
            
            # ============================================
            # ADD USER DURATION BUTTONS
            # ============================================
            
            elif text in ['1h', '6h', '12h', '1d', '3d', '7d', '15d', '30d', '60d', '90d', '180d', '365d', '🔄 Permanent']:
                if chat_id in self.user_context and 'adding_user' in self.user_context[chat_id]:
                    user_id = self.user_context[chat_id]['adding_user']
                    duration = text
                    if text == '🔄 Permanent':
                        duration = 'permanent'
                    self.handle_add_user_with_duration(chat_id, user_id, duration)
                    self.user_context[chat_id] = {}
                else:
                    self.send_message(chat_id, "❌ No user selected! Use /adduser first.", reply_markup=self.get_admin_menu())
            
            # ============================================
            # MONITOR MENU BUTTONS
            # ============================================
            
            elif text == '🎨 Specific Color @ All Stores':
                if chat_id not in self.user_context:
                    self.user_context[chat_id] = {}
                self.user_context[chat_id]['monitor_mode'] = 'specific_color_all_stores'
                self.send_message(chat_id, "🎨 Select a color to monitor at ALL stores: 👇", 
                                reply_markup=self.get_color_menu())
            
            elif text == '🌈 All Colors @ All Stores':
                interval = self.user_context.get(chat_id, {}).get('new_interval', self.default_interval)
                self.monitor_all_colors_all_stores(chat_id, interval)
            
            elif text == '🏪 All Colors @ One Store':
                if chat_id not in self.user_context:
                    self.user_context[chat_id] = {}
                self.user_context[chat_id]['monitor_mode'] = 'all_colors_one_store'
                self.send_message(chat_id, "🏪 Select a store to monitor ALL colors: 👇", 
                                reply_markup=self.get_store_menu())
            
            elif text == '⏱️ Change Monitor Time':
                self.handle_change_interval(chat_id)
            
            # ============================================
            # COLOR SELECTION
            # ============================================
            
            elif text in ['🟣 Lavender', '🟢 Sage', '🔵 Mist Blue', '⚪ White', '⚫ Black']:
                color_name = text.split(' ')[1]
                if text == '🟣 Lavender': color_name = 'Lavender'
                elif text == '🟢 Sage': color_name = 'Sage'
                elif text == '🔵 Mist Blue': color_name = 'Mist Blue'
                elif text == '⚪ White': color_name = 'White'
                elif text == '⚫ Black': color_name = 'Black'
                
                monitor_mode = self.user_context.get(chat_id, {}).get('monitor_mode')
                
                if monitor_mode == 'specific_color_all_stores':
                    interval = self.user_context.get(chat_id, {}).get('new_interval', self.default_interval)
                    self.monitor_specific_color_all_stores(chat_id, color_name, interval)
                    if chat_id in self.user_context:
                        self.user_context[chat_id] = {}
                else:
                    self.handle_color_selection(chat_id, color_name)
            
            # ============================================
            # STORE SELECTION
            # ============================================
            
            elif text in ['Saket', 'Noida', 'BKC', 'Borivali', 'Hebbal', 'Koregaon Park']:
                monitor_mode = self.user_context.get(chat_id, {}).get('monitor_mode')
                
                if monitor_mode == 'all_colors_one_store':
                    interval = self.user_context.get(chat_id, {}).get('new_interval', self.default_interval)
                    self.monitor_all_colors_one_store(chat_id, text, interval)
                    if chat_id in self.user_context:
                        self.user_context[chat_id] = {}
                else:
                    self.handle_store_selection(chat_id, text)
            
            # ============================================
            # INTERVAL PRESETS
            # ============================================
            
            elif text in self.preset_intervals:
                if self.user_context.get(chat_id, {}).get('changing_interval'):
                    self.handle_set_interval(chat_id, text)
                else:
                    self.send_message(chat_id, "❌ Use ⏱️ Change Monitor Time button first!", reply_markup=self.get_main_menu(chat_id))
            
            elif text == '✏️ Custom Time':
                if self.user_context.get(chat_id, {}).get('changing_interval'):
                    self.send_message(chat_id, 
                        "✏️ *Enter custom time in MINUTES*\n\n"
                        "Type a number like:\n"
                        "• 3 (3 minutes)\n"
                        "• 7.5 (7.5 minutes)\n"
                        "• 20 (20 minutes)\n\n"
                        "⏱️ Min: 0.5 min | Max: 60 min\n\n"
                        "Type /cancel to go back.",
                        parse_mode="Markdown",
                        reply_markup=self.get_interval_menu()
                    )
                else:
                    self.send_message(chat_id, "❌ Use ⏱️ Change Monitor Time button first!", reply_markup=self.get_main_menu(chat_id))
            
            # ============================================
            # CUSTOM TIME INPUT
            # ============================================
            
            elif self.user_context.get(chat_id, {}).get('changing_interval'):
                parsed = self.parse_time_input(text)
                if parsed is not None:
                    self.handle_set_interval(chat_id, text)
                else:
                    self.send_message(chat_id, 
                        "❌ Invalid input! Please enter a number in MINUTES.\n"
                        "Example: 3, 7.5, 15, 30\n\n"
                        "Or use the preset buttons.",
                        reply_markup=self.get_interval_menu()
                    )
            
            # ============================================
            # TEXT COMMANDS
            # ============================================
            
            elif text in self.checker.colors:
                self.handle_color_selection(chat_id, text)
            
            elif text in self.checker.stores:
                self.handle_store_selection(chat_id, text)
            
            elif text.startswith('/'):
                if text == '/start':
                    self.handle_start(chat_id)
                elif text == '/help':
                    self.handle_help(chat_id)
                elif text == '/check':
                    self.handle_check_all(chat_id)
                elif text == '/status':
                    self.handle_status(chat_id)
                elif text == '/stop':
                    self.handle_stop_monitor(chat_id)
                elif text == '/cancel':
                    if chat_id in self.user_context:
                        self.user_context[chat_id] = {}
                    self.send_message(chat_id, "❌ Cancelled!", reply_markup=self.get_main_menu(chat_id))
                else:
                    self.send_message(chat_id, "❌ Unknown command. Use the buttons below! 👇", reply_markup=self.get_main_menu(chat_id))
            else:
                self.send_message(chat_id, 
                    "❌ I didn't understand that.\n\n"
                    "💡 Try using the buttons below or type:\n"
                    "• A color name (Lavender, Sage, etc.)\n"
                    "• A store name (Saket, Noida, etc.)\n"
                    "• A number (3, 7.5, 15) for custom time\n"
                    "• /help for more options",
                    reply_markup=self.get_main_menu(chat_id)
                )
                
        except Exception as e:
            logger.error(f"Error processing update: {e}")

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    bot = TelegramStockBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
        bot.running = False
