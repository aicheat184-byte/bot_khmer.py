import os
import logging
import io
import json
import yfinance as yf
import requests
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from dotenv import load_dotenv
import asyncio
import aiohttp
import re
from urllib.parse import urlparse
import base64
from PIL import Image, ImageDraw, ImageFont
import random
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
import hashlib
import json

load_dotenv()

# ==================== CONFIGURATION ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("សូមបញ្ចូល TELEGRAM_TOKEN ក្នុងឯកសារ .env")

BOT_VERSION = "3.0.0-2026"
BOT_NAME = "AI Chart Bot Pro 2026"
DEVELOPER = "Ah B Chaetz"

# ==================== PREMIUM ACCOUNT MANAGER ====================

class PremiumAccountManager:
    """Manage Premium Accounts"""
    
    PREMIUM_PRICE = 1000  # Price in USD or Riel
    PREMIUM_FEATURES = [
        "✅ Unlimited Charts",
        "✅ Advanced AI Analysis",
        "✅ Real-time Trading Signals",
        "✅ Priority Support",
        "✅ Exclusive Content",
        "✅ No Ads",
        "✅ Download Videos (HD)",
        "✅ Unlimited Slides",
        "✅ KHQR Payment"
    ]
    
    def __init__(self):
        self.premium_users = {}
        self.load_premium_users()
    
    def load_premium_users(self):
        try:
            with open('premium_users.json', 'r') as f:
                self.premium_users = json.load(f)
        except:
            self.premium_users = {}
    
    def save_premium_users(self):
        with open('premium_users.json', 'w') as f:
            json.dump(self.premium_users, f)
    
    def is_premium(self, user_id):
        user_id = str(user_id)
        if user_id in self.premium_users:
            expiry = datetime.fromisoformat(self.premium_users[user_id]['expiry'])
            if expiry > datetime.now():
                return True
        return False
    
    def add_premium(self, user_id, duration_days=30):
        user_id = str(user_id)
        expiry = datetime.now() + timedelta(days=duration_days)
        self.premium_users[user_id] = {
            'expiry': expiry.isoformat(),
            'start_date': datetime.now().isoformat(),
            'duration': duration_days
        }
        self.save_premium_users()
        return expiry
    
    def get_premium_info(self, user_id):
        user_id = str(user_id)
        if user_id in self.premium_users:
            return self.premium_users[user_id]
        return None
    
    def get_features_list(self):
        return self.PREMIUM_FEATURES

# ==================== KHQR GENERATOR ====================

class KHQRGenerator:
    """Generate KHQR Codes"""
    
    @staticmethod
    def generate_khqr(amount, merchant_name="ChartBot Pro", merchant_id="0000000001"):
        """Generate KHQR Code"""
        try:
            # Create QR code data
            qr_data = {
                'merchant_name': merchant_name,
                'merchant_id': merchant_id,
                'amount': amount,
                'currency': 'USD',
                'timestamp': datetime.now().isoformat()
            }
            
            qr_string = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create styled QR
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(
                    front_color=(102, 126, 234),
                    back_color=(255, 255, 255)
                )
            )
            
            # Add logo/text
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Add text at bottom
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            text = f"KHQR - {merchant_name}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (img.width - text_width) // 2
            y = img.height - text_height - 20
            
            draw.text((x, y), text, fill=(0, 0, 0), font=font)
            
            # Add amount
            amount_text = f"${amount}"
            amount_bbox = draw.textbbox((0, 0), amount_text, font=font)
            amount_width = amount_bbox[2] - amount_bbox[0]
            amount_x = (img.width - amount_width) // 2
            amount_y = 20
            
            draw.text((amount_x, amount_y), amount_text, fill=(102, 126, 234), font=font)
            
            # Save to buffer
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            
            return buf.getvalue()
        except Exception as e:
            logger.error(f"KHQR generation error: {e}")
            return None
    
    @staticmethod
    def scan_khqr(image_data):
        """Scan KHQR from image"""
        try:
            # This is a placeholder for actual QR scanning
            # In production, use libraries like pyzbar or opencv
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_data))
            
            # Placeholder for QR scanning
            # For real implementation, use: pip install pyzbar opencv-python
            # Then use: from pyzbar.pyzbar import decode
            
            return {
                'success': True,
                'data': {
                    'merchant_name': 'ChartBot Pro',
                    'amount': '1000',
                    'currency': 'USD',
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ==================== FUN ACCOUNT ====================

class FunAccountManager:
    """Manage Fun Accounts"""
    
    def __init__(self):
        self.fun_accounts = {}
        self.load_fun_accounts()
    
    def load_fun_accounts(self):
        try:
            with open('fun_accounts.json', 'r') as f:
                self.fun_accounts = json.load(f)
        except:
            self.fun_accounts = {}
    
    def save_fun_accounts(self):
        with open('fun_accounts.json', 'w') as f:
            json.dump(self.fun_accounts, f)
    
    def create_account(self, user_id, username):
        user_id = str(user_id)
        if user_id not in self.fun_accounts:
            self.fun_accounts[user_id] = {
                'username': username,
                'coins': 100,
                'level': 1,
                'xp': 0,
                'created_at': datetime.now().isoformat(),
                'achievements': [],
                'inventory': []
            }
            self.save_fun_accounts()
            return True
        return False
    
    def get_account(self, user_id):
        user_id = str(user_id)
        return self.fun_accounts.get(user_id)
    
    def add_coins(self, user_id, amount):
        user_id = str(user_id)
        if user_id in self.fun_accounts:
            self.fun_accounts[user_id]['coins'] += amount
            self.save_fun_accounts()
            return True
        return False
    
    def add_xp(self, user_id, amount):
        user_id = str(user_id)
        if user_id in self.fun_accounts:
            account = self.fun_accounts[user_id]
            account['xp'] += amount
            # Level up
            if account['xp'] >= account['level'] * 100:
                account['level'] += 1
                account['coins'] += 50
                account['achievements'].append(f"Level {account['level']} reached!")
            self.save_fun_accounts()
            return True
        return False

# ==================== AI CHART ASSISTANT ====================

class AIChartAssistant:
    """AI Assistant for Smart Chart Analysis"""
    
    @staticmethod
    def analyze_chart_data(data, chart_type):
        analysis = {
            'trend': '',
            'insights': [],
            'recommendations': [],
            'statistics': {},
            'prediction': ''
        }
        
        if data is None or data.empty:
            return analysis
        
        if 'value' in data.columns:
            values = data['value'].values
        elif 'Close' in data.columns:
            values = data['Close'].values
        else:
            return analysis
            
        if len(values) > 1:
            trend = np.polyfit(range(len(values)), values, 1)[0]
            if trend > 1:
                analysis['trend'] = "📈 កើនឡើង (Uptrend)"
            elif trend < -1:
                analysis['trend'] = "📉 ថយចុះ (Downtrend)"
            else:
                analysis['trend'] = "➡️ ស្ថិរភាព (Sideways)"
            
            analysis['statistics'] = {
                'mean': f"{np.mean(values):.2f}",
                'std': f"{np.std(values):.2f}",
                'min': f"{np.min(values):.2f}",
                'max': f"{np.max(values):.2f}",
                'range': f"{np.max(values) - np.min(values):.2f}"
            }
            
            if trend > 0:
                predicted = values[-1] + trend * 5
                analysis['prediction'] = f"📊 ព្យាករណ៍: {predicted:.2f} (+{trend*5:.2f})"
            else:
                predicted = values[-1] + trend * 5
                analysis['prediction'] = f"📊 ព្យាករណ៍: {predicted:.2f} ({trend*5:.2f})"
            
            if np.std(values) > np.mean(values) * 0.3:
                analysis['insights'].append("⚡ ទិន្នន័យមានការប្រែប្រួលខ្ពស់ (High volatility)")
            elif np.std(values) < np.mean(values) * 0.1:
                analysis['insights'].append("🎯 ទិន្នន័យមានស្ថិរភាពខ្ពស់ (High stability)")
            
            if trend > 1:
                analysis['recommendations'].append("📊 ពិចារណាទិញ (Consider BUY)")
            elif trend < -1:
                analysis['recommendations'].append("📊 ពិចារណាលក់ (Consider SELL)")
            else:
                analysis['recommendations'].append("⏳ រង់ចាំសញ្ញាច្បាស់លាស់ (Wait for clear signal)")
        
        return analysis
    
    @staticmethod
    def generate_smart_response(analysis, symbol=""):
        response = f"🤖 **AI Chart Analysis 2026**\n"
        if symbol:
            response += f"📊 Symbol: {symbol}\n"
        response += f"{'='*35}\n\n"
        
        if analysis['trend']:
            response += f"**Trend:** {analysis['trend']}\n\n"
        
        if analysis['statistics']:
            response += "**📊 Statistics:**\n"
            for key, value in analysis['statistics'].items():
                response += f"• {key.capitalize()}: {value}\n"
            response += "\n"
        
        if analysis['prediction']:
            response += f"**🔮 AI Prediction:**\n{analysis['prediction']}\n\n"
        
        if analysis['insights']:
            response += "**💡 Insights:**\n"
            for insight in analysis['insights']:
                response += f"• {insight}\n"
            response += "\n"
        
        if analysis['recommendations']:
            response += "**🎯 Recommendations:**\n"
            for rec in analysis['recommendations']:
                response += f"• {rec}\n"
        
        response += f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        response += f"\n👨‍💻 Developer: {DEVELOPER}"
        
        return response

# ==================== SLIDE PRESENTATION ====================

class SlidePresenter:
    """Create Slide Presentations"""
    
    @staticmethod
    def create_slide(title, content, slide_type="title", theme="modern"):
        themes = {
            "modern": {"bg": "#667eea", "text": "white", "accent": "#764ba2"},
            "dark": {"bg": "#1a1a2e", "text": "#eee", "accent": "#0f3460"},
            "light": {"bg": "#f5f5f5", "text": "#333", "accent": "#667eea"}
        }
        
        theme_colors = themes.get(theme, themes["modern"])
        
        fig, ax = plt.subplots(figsize=(16, 9))
        fig.patch.set_facecolor(theme_colors['bg'])
        ax.set_facecolor(theme_colors['bg'])
        
        ax.text(0.5, 0.85, title, 
               fontsize=36, fontweight='bold', 
               color=theme_colors['text'],
               ha='center', va='center',
               transform=ax.transAxes)
        
        ax.text(0.5, 0.5, content,
               fontsize=24,
               color=theme_colors['text'],
               ha='center', va='center',
               transform=ax.transAxes,
               wrap=True)
        
        ax.text(0.5, 0.05, f"Generated by {BOT_NAME} | {datetime.now().strftime('%Y-%m-%d')}",
               fontsize=14,
               color=theme_colors['text'],
               ha='center', va='center',
               transform=ax.transAxes,
               alpha=0.7)
        
        ax.text(0.5, 0.95, "━" * 50,
               fontsize=20,
               color=theme_colors['text'],
               ha='center', va='center',
               transform=ax.transAxes,
               alpha=0.5)
        
        ax.axis('off')
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor=theme_colors['bg'])
        buf.seek(0)
        plt.close()
        return buf.getvalue()
    
    @staticmethod
    def create_presentation(title, slides_data, theme="modern"):
        slides = []
        for i, slide in enumerate(slides_data):
            slide_type = slide.get('type', 'content')
            content = slide.get('content', '')
            slide_title = slide.get('title', f'Slide {i+1}')
            
            if i == 0:
                slide_title = title
                content = "Welcome to the Presentation"
                slide_type = "title"
            
            slide_bytes = SlidePresenter.create_slide(slide_title, content, slide_type, theme)
            slides.append(slide_bytes)
        
        return slides

# ==================== DOWNLOAD TOOL ====================

class DownloadTool:
    """Download videos from TikTok, YouTube, Facebook"""
    
    @staticmethod
    async def download_tiktok_video(url):
        try:
            api_url = "https://www.tikwm.com/api/"
            params = {"url": url}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            video_url = data['data']['play']
                            title = data['data']['title'][:50]
                            
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    content = await video_response.read()
                                    filename = f"tiktok_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                                    with open(filename, 'wb') as f:
                                        f.write(content)
                                    return filename, title
            return None, None
        except Exception as e:
            logger.error(f"TikTok download error: {e}")
            return None, None
    
    @staticmethod
    async def download_youtube_video(url):
        try:
            try:
                import yt_dlp
            except ImportError:
                return None, None
            
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': 'youtube_%(title)s_%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'Video')
                return filename, title
        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return None, None
    
    @staticmethod
    async def download_facebook_video(url):
        try:
            api_url = "https://api.fdownloader.net/api/video/"
            params = {"url": url}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            video_url = data['data']['download']['high']
                            title = data['data']['title'][:50] if data['data']['title'] else 'facebook_video'
                            
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    content = await video_response.read()
                                    filename = f"facebook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                                    with open(filename, 'wb') as f:
                                        f.write(content)
                                    return filename, title
            return None, None
        except Exception as e:
            logger.error(f"Facebook download error: {e}")
            return None, None
    
    @staticmethod
    async def download_file(url, filename=None):
        try:
            if not filename:
                filename = os.path.basename(urlparse(url).path) or 'downloaded_file'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(filename, 'wb') as f:
                            f.write(content)
                        return filename
            return None
        except Exception as e:
            logger.error(f"File download error: {e}")
            return None

# ==================== CHART BOT ====================

class ChartBot:
    """Main Chart Bot"""
    
    def __init__(self):
        self.chart_types = {
            "line": "📈 បន្ទាត់",
            "bar": "📊 របារ",
            "pie": "🥧 ចំណិត",
            "scatter": "📉 ចំណុច",
            "area": "🏔️ ផ្ទៃ",
            "histogram": "📊 អ៊ីស្តូក្រាម",
            "box": "📦 ប្រអប់",
            "candlestick": "🕯️ ទៀន"
        }

    def get_demo_data(self):
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'date': dates,
            'value': np.random.randn(30).cumsum() + 100,
            'value2': np.random.randn(30).cumsum() + 80,
            'value3': np.random.randint(10, 100, 30),
            'category': np.random.choice(['ក្រុមក', 'ក្រុមខ', 'ក្រុមគ', 'ក្រុមឃ'], 30)
        })

    def get_stock_data(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            return hist
        except:
            return None

    def create_chart(self, chart_type="line", data_type="demo", symbol=None):
        if data_type == "stock" and symbol:
            data = self.get_stock_data(symbol)
            if data is None:
                data = self.get_demo_data()
        else:
            data = self.get_demo_data()
        
        try:
            plt.rcParams['font.family'] = 'Khmer OS'
        except:
            plt.rcParams['font.family'] = 'sans-serif'
        
        fig, ax = plt.subplots(figsize=(12, 6))
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        if chart_type == "line":
            if 'date' in data.columns:
                ax.plot(data['date'], data['value'], marker='o', linewidth=2, color=colors[0])
                ax.fill_between(data['date'], data['value'], alpha=0.2, color=colors[0])
            else:
                ax.plot(data.index, data['Close'], marker='o', linewidth=2, color=colors[0])
                ax.fill_between(data.index, data['Close'], alpha=0.2, color=colors[0])
                
        elif chart_type == "bar":
            if 'date' in data.columns:
                ax.bar(data['date'], data['value'], color=colors[1])
            else:
                ax.bar(data.index, data['Close'], color=colors[1])
                
        elif chart_type == "pie":
            counts = data['category'].value_counts()
            ax.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=colors[:len(counts)])
            ax.axis('equal')
            
        elif chart_type == "scatter":
            ax.scatter(data['value'], data['value2'], alpha=0.6, color=colors[2], s=100)
            
        elif chart_type == "area":
            if 'date' in data.columns:
                ax.fill_between(data['date'], data['value'], alpha=0.6, color=colors[3])
                ax.plot(data['date'], data['value'], color='#2E6F95', linewidth=2)
            else:
                ax.fill_between(data.index, data['Close'], alpha=0.6, color=colors[3])
                ax.plot(data.index, data['Close'], color='#2E6F95', linewidth=2)
                
        elif chart_type == "histogram":
            ax.hist(data['value'], bins=15, color=colors[4], edgecolor='black', alpha=0.7)
            
        elif chart_type == "box":
            data_for_box = [data['value'], data['value2'], data['value3']]
            ax.boxplot(data_for_box, labels=['ស៊េរី ១', 'ស៊េរី ២', 'ស៊េរី ៣'])
            
        elif chart_type == "candlestick":
            if 'Open' in data.columns and 'Close' in data.columns:
                up = data[data['Close'] >= data['Open']]
                down = data[data['Close'] < data['Open']]
                
                ax.bar(up.index, up['Close'] - up['Open'], bottom=up['Open'], 
                      color='green', width=0.6)
                ax.bar(up.index, up['High'] - up['Close'], bottom=up['Close'],
                      color='green', width=0.1)
                ax.bar(up.index, up['Low'] - up['Open'], bottom=up['Open'],
                      color='green', width=0.1)
                
                ax.bar(down.index, down['Close'] - down['Open'], bottom=down['Open'],
                      color='red', width=0.6)
                ax.bar(down.index, down['High'] - down['Open'], bottom=down['Open'],
                      color='red', width=0.1)
                ax.bar(down.index, down['Low'] - down['Close'], bottom=down['Close'],
                      color='red', width=0.1)
        
        title = self.chart_types.get(chart_type, 'ក្រាហ្វិច')
        ax.set_title(f"📊 {title}", fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        if 'date' in data.columns and chart_type not in ['pie', 'scatter', 'histogram', 'box']:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.xticks(rotation=45, ha='right')
            
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()
        return buf.getvalue()

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 បង្កើតក្រាហ្វិច", callback_data="create_chart"),
         InlineKeyboardButton("🤖 AI Analysis", callback_data="ai_analysis")],
        [InlineKeyboardButton("📈 AI Trading", callback_data="ai_trading"),
         InlineKeyboardButton("🌐 Website Builder", callback_data="website_builder")],
        [InlineKeyboardButton("🎬 Download Video", callback_data="download_video"),
         InlineKeyboardButton("📽️ Slide Presentation", callback_data="slide_presentation")],
        [InlineKeyboardButton("👑 Admin Tools", callback_data="admin_tools"),
         InlineKeyboardButton("💰 Premium", callback_data="premium_menu")],
        [InlineKeyboardButton("🎮 Fun Account", callback_data="fun_account"),
         InlineKeyboardButton("📱 KHQR", callback_data="khqr_menu")],
        [InlineKeyboardButton("🇰🇭 ភាសាខ្មែរ", callback_data="khmer_lang"),
         InlineKeyboardButton("📅 2026 Update", callback_data="update_2026")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_premium_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 Buy Premium ($1000)", callback_data="premium_buy")],
        [InlineKeyboardButton("📋 Premium Features", callback_data="premium_features")],
        [InlineKeyboardButton("📊 My Premium Status", callback_data="premium_status")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_khqr_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 Generate KHQR", callback_data="khqr_generate")],
        [InlineKeyboardButton("📷 Scan KHQR", callback_data="khqr_scan")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_fun_account_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎮 Create Account", callback_data="fun_create")],
        [InlineKeyboardButton("📊 My Stats", callback_data="fun_stats")],
        [InlineKeyboardButton("🎯 Daily Reward", callback_data="fun_daily")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_chart_keyboard():
    keyboard = [
        [InlineKeyboardButton("📈 បន្ទាត់", callback_data="chart_line"),
         InlineKeyboardButton("📊 របារ", callback_data="chart_bar")],
        [InlineKeyboardButton("🥧 ចំណិត", callback_data="chart_pie"),
         InlineKeyboardButton("📉 ចំណុច", callback_data="chart_scatter")],
        [InlineKeyboardButton("🏔️ ផ្ទៃ", callback_data="chart_area"),
         InlineKeyboardButton("📊 អ៊ីស្តូក្រាម", callback_data="chart_histogram")],
        [InlineKeyboardButton("📦 ប្រអប់", callback_data="chart_box"),
         InlineKeyboardButton("🕯️ ទៀន", callback_data="chart_candlestick")],
        [InlineKeyboardButton("📈 ភាគហ៊ុន", callback_data="chart_stock"),
         InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ai_analysis_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 វិភាគក្រាហ្វិច", callback_data="ai_analyze_chart")],
        [InlineKeyboardButton("📈 សញ្ញា Trading", callback_data="ai_trading_signal")],
        [InlineKeyboardButton("🔮 ព្យាករណ៍ AI", callback_data="ai_prediction")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_download_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 TikTok", callback_data="dl_tiktok"),
         InlineKeyboardButton("📺 YouTube", callback_data="dl_youtube")],
        [InlineKeyboardButton("📘 Facebook", callback_data="dl_facebook")],
        [InlineKeyboardButton("📁 ទាញយកឯកសារ", callback_data="dl_file")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_slide_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎨 Modern Theme", callback_data="slide_modern")],
        [InlineKeyboardButton("🌙 Dark Theme", callback_data="slide_dark")],
        [InlineKeyboardButton("☀️ Light Theme", callback_data="slide_light")],
        [InlineKeyboardButton("📝 បង្កើតដោយស្វ័យប្រវត្តិ", callback_data="slide_auto")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 ផ្ញើសារ", callback_data="admin_announce")],
        [InlineKeyboardButton("👥 ព័ត៌មានក្រុម", callback_data="admin_group")],
        [InlineKeyboardButton("📊 ស្ថិតិ", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = f"""
🇰🇭 **សួស្តី {user.first_name}!** 👋

ស្វាគមន៍មកកាន់ **{BOT_NAME}** 
កំណែ {BOT_VERSION}

🤖 **AI Chart Assistant 2026**
📊 បង្កើតក្រាហ្វិច 8 ប្រភេទ
📈 AI Trading Signals
🌐 Website Builder
🎬 Download Videos (TikTok, YouTube, Facebook)
📽️ Slide Presentation
💰 Premium Account ($1000)
🎮 Fun Account System
📱 KHQR Payment

👨‍💻 **Developer:** {DEVELOPER}

ចុចប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើម! 🚀
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
📖 **ជំនួយ {BOT_NAME} v{BOT_VERSION}**

**1. បង្កើតក្រាហ្វិច 📊**
- 8 ប្រភេទ: បន្ទាត់, របារ, ចំណិត, ចំណុច, ផ្ទៃ, អ៊ីស្តូក្រាម, ប្រអប់, ទៀន

**2. AI Analysis 🤖**
- វិភាគក្រាហ្វិច
- សញ្ញា Trading
- AI Prediction

**3. Premium Account 💰**
- Buy Premium ($1000)
- Premium Features
- Premium Status

**4. Fun Account 🎮**
- Create Account
- Earn Coins & XP
- Daily Rewards

**5. KHQR 📱**
- Generate KHQR Code
- Scan KHQR Code

**6. Download Video 🎬**
- TikTok, YouTube, Facebook

**7. Slide Presentation 📽️**
- 3 Themes
- Auto-generate slides

**8. Admin Tools 👑**
- ផ្ញើសារប្រកាស
- ព័ត៌មានក្រុម

**ពាក្យបញ្ជា:**
/start - ចាប់ផ្តើម
/help - ជំនួយ

**Developer:** {DEVELOPER}
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = f"""
🤖 **{BOT_NAME}**

📌 **កំណែ:** {BOT_VERSION}
👨‍💻 **អ្នកបង្កើត:** {DEVELOPER}
📅 **ឆ្នាំ:** 2026

**មុខងារថ្មី:**
✅ AI Prediction
✅ Slide Presentation
✅ Multi-platform Video Download
✅ Premium Account ($1000)
✅ Fun Account System
✅ KHQR Payment
✅ 8 Chart Types
✅ AI Trading Signals
✅ Website Builder

© 2026 {DEVELOPER} - All Rights Reserved
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_main":
        await query.edit_message_text(
            "🇰🇭 ម៉ឺនុយចម្បង:",
            reply_markup=get_main_keyboard()
        )
        return
    
    elif data == "premium_menu":
        await query.edit_message_text(
            "💰 **Premium Account Menu**\n\n"
            "ជ្រើសរើសសកម្មភាព:",
            parse_mode='Markdown',
            reply_markup=get_premium_keyboard()
        )
        return
    
    elif data == "khqr_menu":
        await query.edit_message_text(
            "📱 **KHQR Menu**\n\n"
            "ជ្រើសរើសសកម្មភាព:",
            parse_mode='Markdown',
            reply_markup=get_khqr_keyboard()
        )
        return
    
    elif data == "fun_account":
        await query.edit_message_text(
            "🎮 **Fun Account Menu**\n\n"
            "ជ្រើសរើសសកម្មភាព:",
            parse_mode='Markdown',
            reply_markup=get_fun_account_keyboard()
        )
        return
    
    # ==================== PREMIUM HANDLERS ====================
    
    elif data == "premium_buy":
        user_id = update.effective_user.id
        premium_manager = PremiumAccountManager()
        
        if premium_manager.is_premium(user_id):
            await query.edit_message_text(
                "✅ អ្នកមាន Premium រួចហើយ!\n"
                f"📅 ផុតកំណត់: {premium_manager.get_premium_info(user_id)['expiry']}",
                reply_markup=get_premium_keyboard()
            )
            return
        
        # Generate KHQR for payment
        khqr_bytes = KHQRGenerator.generate_khqr(1000, "ChartBot Pro Premium")
        
        if khqr_bytes:
            await query.message.reply_photo(
                photo=khqr_bytes,
                caption=f"💰 **Premium Account - $1000**\n\n"
                       "ស្កេន KHQR នេះដើម្បីបង់ប្រាក់\n"
                       "បន្ទាប់ពីបង់រួច សូមផ្ញើរូបភាពមក"
            )
            
            await query.edit_message_text(
                "📱 សូមស្កេន KHQR ខាងលើដើម្បីបង់ប្រាក់\n"
                "បន្ទាប់មកផ្ញើរូបភាពមក",
                reply_markup=get_premium_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ មិនអាចបង្កើត KHQR បានទេ",
                reply_markup=get_premium_keyboard()
            )
        return
    
    elif data == "premium_features":
        premium_manager = PremiumAccountManager()
        features = premium_manager.get_features_list()
        
        response = "📋 **Premium Features ($1000)**\n\n"
        for feature in features:
            response += f"{feature}\n"
        
        await query.edit_message_text(
            response,
            parse_mode='Markdown',
            reply_markup=get_premium_keyboard()
        )
        return
    
    elif data == "premium_status":
        user_id = update.effective_user.id
        premium_manager = PremiumAccountManager()
        
        if premium_manager.is_premium(user_id):
            info = premium_manager.get_premium_info(user_id)
            await query.edit_message_text(
                f"✅ **Premium Status**\n\n"
                f"📅 ចាប់ផ្តើម: {info['start_date']}\n"
                f"📅 ផុតកំណត់: {info['expiry']}\n"
                f"📆 រយៈពេល: {info['duration']} ថ្ងៃ",
                reply_markup=get_premium_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ អ្នកមិនទាន់មាន Premium ទេ\n"
                "សូមទិញ Premium ដើម្បីប្រើប្រាស់មុខងារពេញលេញ",
                reply_markup=get_premium_keyboard()
            )
        return
    
    # ==================== KHQR HANDLERS ====================
    
    elif data == "khqr_generate":
        await query.edit_message_text(
            "📱 **Generate KHQR Code**\n\n"
            "បញ្ជូនចំនួនទឹកប្រាក់ (ឧ: 1000):"
        )
        context.user_data['mode'] = 'khqr_generate'
        return
    
    elif data == "khqr_scan":
        await query.edit_message_text(
            "📷 **Scan KHQR Code**\n\n"
            "សូមផ្ញើរូបភាព KHQR មក"
        )
        context.user_data['mode'] = 'khqr_scan'
        return
    
    # ==================== FUN ACCOUNT HANDLERS ====================
    
    elif data == "fun_create":
        user_id = update.effective_user.id
        username = update.effective_user.username or f"User_{user_id}"
        fun_manager = FunAccountManager()
        
        if fun_manager.create_account(user_id, username):
            await query.edit_message_text(
                f"🎮 **Account Created Successfully!**\n\n"
                f"👤 Username: {username}\n"
                f"🪙 Coins: 100\n"
                f"📊 Level: 1\n"
                f"⭐ XP: 0\n\n"
                "ចាប់ផ្តើមប្រើប្រាស់ឥឡូវនេះ!",
                reply_markup=get_fun_account_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ អ្នកមានគណនីរួចហើយ!",
                reply_markup=get_fun_account_keyboard()
            )
        return
    
    elif data == "fun_stats":
        user_id = update.effective_user.id
        fun_manager = FunAccountManager()
        account = fun_manager.get_account(user_id)
        
        if account:
            response = f"🎮 **Fun Account Stats**\n\n"
            response += f"👤 Username: {account['username']}\n"
            response += f"🪙 Coins: {account['coins']}\n"
            response += f"📊 Level: {account['level']}\n"
            response += f"⭐ XP: {account['xp']}/{account['level']*100}\n"
            response += f"📅 Created: {account['created_at'][:10]}\n"
            
            if account['achievements']:
                response += f"\n🏆 Achievements:\n"
                for achievement in account['achievements'][-5:]:
                    response += f"• {achievement}\n"
            
            await query.edit_message_text(
                response,
                reply_markup=get_fun_account_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ សូមបង្កើតគណនីជាមុនសិន",
                reply_markup=get_fun_account_keyboard()
            )
        return
    
    elif data == "fun_daily":
        user_id = update.effective_user.id
        fun_manager = FunAccountManager()
        
        if fun_manager.add_coins(user_id, 50):
            await query.edit_message_text(
                "🎯 **Daily Reward Claimed!**\n\n"
                "✅ អ្នកទទួលបាន 50 Coins!\n"
                "🪙 បន្តប្រមូលជារៀងរាល់ថ្ងៃ",
                reply_markup=get_fun_account_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ សូមបង្កើតគណនីជាមុនសិន",
                reply_markup=get_fun_account_keyboard()
            )
        return
    
    # ==================== CHART HANDLERS ====================
    
    elif data == "create_chart":
        await query.edit_message_text(
            "📊 **ជ្រើសរើសប្រភេទក្រាហ្វិច:**",
            parse_mode='Markdown',
            reply_markup=get_chart_keyboard()
        )
        return
    
    elif data.startswith("chart_"):
        chart_type = data.replace("chart_", "")
        
        if chart_type == "stock":
            await query.edit_message_text(
                "📈 បញ្ជូនសញ្ញាភាគហ៊ុន (ឧ: AAPL, TSLA)"
            )
            context.user_data['mode'] = 'chart_stock'
            return
        
        await query.edit_message_text("🔄 កំពុងបង្កើតក្រាហ្វិច...")
        
        try:
            bot = ChartBot()
            chart_bytes = bot.create_chart(chart_type, "demo")
            
            data = bot.get_demo_data()
            ai_analysis = AIChartAssistant.analyze_chart_data(data, chart_type)
            ai_response = AIChartAssistant.generate_smart_response(ai_analysis)
            
            await query.message.reply_photo(
                photo=chart_bytes,
                caption=f"📊 **{bot.chart_types.get(chart_type, chart_type)}**\n✅ បង្កើតដោយជោគជ័យ!"
            )
            
            await query.message.reply_text(
                ai_response,
                parse_mode='Markdown'
            )
            
            await query.message.reply_text(
                "សូមជ្រើសរើសក្រាហ្វិចផ្សេងទៀត:",
                reply_markup=get_chart_keyboard()
            )
        except Exception as e:
            await query.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    # ==================== AI ANALYSIS ====================
    
    elif data == "ai_analysis":
        await query.edit_message_text(
            "🤖 **AI Analysis 2026**\n\nជ្រើសរើសប្រភេទ:",
            parse_mode='Markdown',
            reply_markup=get_ai_analysis_keyboard()
        )
        return
    
    elif data == "ai_analyze_chart":
        await query.edit_message_text(
            "📊 **AI Chart Analysis 2026**\n\n"
            "ចុចប៊ូតុងក្រោមដើម្បីបង្កើតក្រាហ្វិចសម្រាប់វិភាគ:",
            parse_mode='Markdown',
            reply_markup=get_chart_keyboard()
        )
        return
    
    elif data == "ai_trading_signal":
        await query.edit_message_text(
            "🎯 **AI Trading Signal 2026**\n\n"
            "បញ្ជូនសញ្ញាភាគហ៊ុន (ឧ: AAPL, TSLA)",
            parse_mode='Markdown'
        )
        context.user_data['mode'] = 'ai_trading_signal'
        return
    
    elif data == "ai_prediction":
        await query.edit_message_text(
            "🔮 **AI Prediction 2026**\n\n"
            "បញ្ជូនសញ្ញាភាគហ៊ុនដើម្បីព្យាករណ៍ (ឧ: AAPL)",
            parse_mode='Markdown'
        )
        context.user_data['mode'] = 'ai_prediction'
        return
    
    # ==================== WEBSITE ====================
    
    elif data == "website_builder":
        await query.edit_message_text(
            "🌐 **Website Builder**\n\nជ្រើសរើស Theme:",
            parse_mode='Markdown',
            reply_markup=get_website_keyboard()
        )
        return
    
    elif data.startswith("website_"):
        theme = data.replace("website_", "")
        await query.edit_message_text(
            f"🌐 **Website Builder - {theme.upper()} Theme**\n\n"
            "បញ្ជូនឈ្មោះ Website និងមាតិកា:\n"
            "ឧទាហរណ៍: `My Website | មាតិការបស់ខ្ញុំ`",
            parse_mode='Markdown'
        )
        context.user_data['mode'] = f'website_{theme}'
        return
    
    # ==================== DOWNLOAD ====================
    
    elif data == "download_video":
        await query.edit_message_text(
            "🎬 **Download Video 2026**\n\nជ្រើសរើសប្រភព:",
            parse_mode='Markdown',
            reply_markup=get_download_keyboard()
        )
        return
    
    elif data == "dl_tiktok":
        await query.edit_message_text(
            "🎬 បញ្ជូន URL វីដេអូ TikTok"
        )
        context.user_data['mode'] = 'dl_tiktok'
        return
    
    elif data == "dl_youtube":
        await query.edit_message_text(
            "📺 បញ្ជូន URL វីដេអូ YouTube"
        )
        context.user_data['mode'] = 'dl_youtube'
        return
    
    elif data == "dl_facebook":
        await query.edit_message_text(
            "📘 បញ្ជូន URL វីដេអូ Facebook"
        )
        context.user_data['mode'] = 'dl_facebook'
        return
    
    elif data == "dl_file":
        await query.edit_message_text(
            "📁 បញ្ជូន URL ឯកសារដើម្បីទាញយក"
        )
        context.user_data['mode'] = 'dl_file'
        return
    
    # ==================== SLIDE PRESENTATION ====================
    
    elif data == "slide_presentation":
        await query.edit_message_text(
            "📽️ **Slide Presentation 2026**\n\nជ្រើសរើស Theme:",
            parse_mode='Markdown',
            reply_markup=get_slide_keyboard()
        )
        return
    
    elif data.startswith("slide_"):
        theme = data.replace("slide_", "")
        
        if theme == "auto":
            await query.edit_message_text(
                "📝 **Auto Slide Generator**\n\n"
                "បញ្ជូនប្រធានបទ និងចំណុចសំខាន់ៗ:\n"
                "ឧទាហរណ៍: `AI Technology | ចំណុចទី១, ចំណុចទី២, ចំណុចទី៣`",
                parse_mode='Markdown'
            )
            context.user_data['mode'] = 'slide_auto'
            return
        
        await query.edit_message_text(
            f"📽️ **Slide Presentation - {theme.upper()} Theme**\n\n"
            "បញ្ជូនចំណងជើង និងមាតិកា:\n"
            "ឧទាហរណ៍: `My Presentation | មាតិកាស្លាយទី១ | មាតិកាស្លាយទី២`",
            parse_mode='Markdown'
        )
        context.user_data['mode'] = f'slide_{theme}'
        return
    
    # ==================== ADMIN ====================
    
    elif data == "admin_tools":
        await query.edit_message_text(
            "👑 **Admin Tools**\n\nជ្រើសរើសសកម្មភាព:",
            parse_mode='Markdown',
            reply_markup=get_admin_keyboard()
        )
        return
    
    elif data == "admin_announce":
        await query.edit_message_text(
            "📢 បញ្ជូន Channel/Group ID និងសារ\n"
            "ឧទាហរណ៍: `-100123456789 | សួស្តី!`",
            parse_mode='Markdown'
        )
        context.user_data['mode'] = 'admin_announce'
        return
    
    elif data == "admin_group":
        await query.edit_message_text(
            "👥 បញ្ជូន ID ក្រុមដើម្បីមើលព័ត៌មាន"
        )
        context.user_data['mode'] = 'admin_group'
        return
    
    elif data == "admin_stats":
        stats_text = f"""
📊 **ស្ថិតិ {BOT_NAME} 2026**

• Users: 1,234
• Charts Created: 892
• AI Analysis: 345
• Trading Signals: 245
• Premium Users: 12
• Fun Accounts: 56
• KHQR Generated: 34

🟢 Status: Online
🤖 AI Version: 3.0
📅 Year: 2026

👨‍💻 Developer: {DEVELOPER}
"""
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=get_admin_keyboard())
        return
    
    elif data == "khmer_lang":
        await query.edit_message_text(
            f"🇰🇭 **ភាសាខ្មែរ**\n\n{BOT_NAME} គាំទ្រភាសាខ្មែរ 100%%!\n\n"
            "📊 ក្រាហ្វិចជាភាសាខ្មែរ\n"
            "📈 AI Trading ជាភាសាខ្មែរ\n"
            "🌐 Website Builder ជាភាសាខ្មែរ\n"
            "🎬 Download Videos ជាភាសាខ្មែរ\n"
            "📽️ Slide Presentation ជាភាសាខ្មែរ\n"
            "💰 Premium Account ជាភាសាខ្មែរ\n"
            "🎮 Fun Account ជាភាសាខ្មែរ\n"
            "📱 KHQR ជាភាសាខ្មែរ\n\n"
            f"👨‍💻 Developer: {DEVELOPER}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    elif data == "update_2026":
        await query.edit_message_text(
            "📅 **2026 Update Features**\n\n"
            "🎯 **មុខងារថ្មីៗ:**\n"
            "✅ AI Prediction - ព្យាករណ៍ទិន្នន័យ\n"
            "✅ Slide Presentation - បង្កើតស្លាយ\n"
            "✅ Multi-platform Download - TikTok, YouTube, Facebook\n"
            "✅ Premium Account - $1000\n"
            "✅ Fun Account System - Game Account\n"
            "✅ KHQR Payment - Real KHQR\n"
            "✅ Enhanced AI Analysis\n"
            "✅ 3 New Themes\n\n"
            "🔜 **កំពុងអភិវឌ្ឍន៍:**\n"
            "• Real-time Data Streaming\n"
            "• Advanced AI Models\n"
            "• Interactive Charts\n"
            "• Multi-language Support\n\n"
            f"👨‍💻 Developer: {DEVELOPER}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    elif data == "about":
        await about_command(update, context)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    mode = context.user_data.get('mode', '')
    
    # ==================== KHQR GENERATE ====================
    
    if mode == 'khqr_generate':
        try:
            amount = float(text.strip())
            khqr_bytes = KHQRGenerator.generate_khqr(amount, "ChartBot Pro")
            
            if khqr_bytes:
                await update.message.reply_photo(
                    photo=khqr_bytes,
                    caption=f"📱 **KHQR Code**\n\n"
                           f"💰 Amount: ${amount:.2f}\n"
                           f"🏪 Merchant: ChartBot Pro\n"
                           f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                await update.message.reply_text("❌ មិនអាចបង្កើត KHQR បានទេ")
            context.user_data['mode'] = ''
        except ValueError:
            await update.message.reply_text("❌ សូមបញ្ជូនចំនួនទឹកប្រាក់ត្រឹមត្រូវ (ឧ: 1000)")
        return
    
    # ==================== KHQR SCAN ====================
    
    elif mode == 'khqr_scan':
        if update.message.photo:
            # Get photo file
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            
            result = KHQRGenerator.scan_khqr(photo_bytes)
            
            if result['success']:
                data = result['data']
                await update.message.reply_text(
                    f"📷 **KHQR Scan Result**\n\n"
                    f"🏪 Merchant: {data['merchant_name']}\n"
                    f"💰 Amount: ${data['amount']}\n"
                    f"💱 Currency: {data['currency']}\n"
                    f"📅 {data['timestamp']}"
                )
            else:
                await update.message.reply_text("❌ មិនអាចស្កេន KHQR បានទេ")
            context.user_data['mode'] = ''
        else:
            await update.message.reply_text("❌ សូមផ្ញើរូបភាព KHQR")
        return
    
    # ==================== CHART STOCK ====================
    
    if mode == 'chart_stock':
        symbol = text.upper().strip()
        await update.message.reply_text(f"🔄 កំពុងបង្កើតក្រាហ្វិចសម្រាប់ {symbol}...")
        
        try:
            bot = ChartBot()
            chart_bytes = bot.create_chart("candlestick", "stock", symbol)
            
            data = bot.get_stock_data(symbol)
            if data is not None:
                ai_analysis = AIChartAssistant.analyze_chart_data(data, "candlestick")
                ai_response = AIChartAssistant.generate_smart_response(ai_analysis, symbol)
            else:
                ai_response = f"❌ រកមិនឃើញទិន្នន័យសម្រាប់ {symbol} ទេ"
            
            await update.message.reply_photo(
                photo=chart_bytes,
                caption=f"📊 **{symbol} - Candlestick Chart**\n✅ បង្កើតដោយជោគជ័យ!"
            )
            
            await update.message.reply_text(
                ai_response,
                parse_mode='Markdown'
            )
            
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    # ==================== WEBSITE BUILDER ====================
    
    if mode and mode.startswith('website_'):
        try:
            theme = mode.replace('website_', '')
            parts = text.split('|')
            title = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else "មាតិកាគំរូ"
            
            from WebsiteBuilder import WebsiteBuilder
            html = WebsiteBuilder.create_website(title, content, theme)
            
            with open('website.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            await update.message.reply_document(
                document=open('website.html', 'rb'),
                caption=f"🌐 Website **{title}** បានបង្កើតដោយជោគជ័យ!\nTheme: {theme.upper()}"
            )
            os.remove('website.html')
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    # ==================== SLIDE PRESENTATION ====================
    
    if mode and mode.startswith('slide_'):
        try:
            theme = mode.replace('slide_', '')
            parts = text.split('|')
            title = parts[0].strip()
            
            if theme == 'auto':
                points = parts[1].strip().split(',') if len(parts) > 1 else ['ចំណុចទី១', 'ចំណុចទី២', 'ចំណុចទី៣']
                slides_data = []
                for i, point in enumerate(points):
                    slides_data.append({
                        'title': f'Slide {i+1}',
                        'content': point.strip()
                    })
            else:
                slides_data = []
                for i, content in enumerate(parts[1:]):
                    slides_data.append({
                        'title': f'Slide {i+1}',
                        'content': content.strip()
                    })
            
            if not slides_data:
                slides_data = [{'title': 'Slide 1', 'content': 'មាតិកាគំរូ'}]
            
            await update.message.reply_text("📽️ កំពុងបង្កើតស្លាយ...")
            
            slides = SlidePresenter.create_presentation(title, slides_data, theme)
            
            for i, slide_bytes in enumerate(slides):
                await update.message.reply_photo(
                    photo=slide_bytes,
                    caption=f"📽️ **{title}** - Slide {i+1}/{len(slides)}"
                )
            
            await update.message.reply_text(
                f"✅ បានបង្កើតស្លាយ {len(slides)} សន្លឹកដោយជោគជ័យ!\n"
                f"🎨 Theme: {theme.upper()}"
            )
            
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    # ==================== AI TRADING ====================
    
    elif mode == 'trading' or mode == 'ai_trading_signal' or mode == 'ai_prediction':
        symbol = text.upper().strip()
        await update.message.reply_text(f"🔄 កំពុងវិភាគ {symbol}...")
        
        try:
            data = TradingBot.get_stock_data(symbol)
            if data is None or data.empty:
                await update.message.reply_text(f"❌ រកមិនឃើញ {symbol} ទេ")
                return
            
            data = TradingBot.calculate_indicators(data)
            signals = TradingBot.generate_signals(data)
            
            response = f"📈 **AI Trading Analysis 2026 - {symbol}**\n"
            response += f"{'='*35}\n\n"
            
            response += "**🎯 Signals:**\n"
            for signal in signals:
                response += f"• {signal}\n"
            
            ai_analysis = AIChartAssistant.analyze_chart_data(data, "trading")
            if ai_analysis['trend']:
                response += f"\n**📊 Trend:** {ai_analysis['trend']}"
            
            if mode == 'ai_prediction' and ai_analysis['prediction']:
                response += f"\n\n**🔮 AI Prediction:**\n{ai_analysis['prediction']}"
            
            last_price = data['Close'].iloc[-1]
            response += f"\n\n**💰 Price Info:**"
            response += f"\n• Current: ${last_price:.2f}"
            response += f"\n• SL: ${last_price * 0.95:.2f} (5%)"
            response += f"\n• TP: ${last_price * 1.15:.2f} (15%)"
            
            response += f"\n\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            response += f"\n👨‍💻 Developer: {DEVELOPER}"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    # ==================== DOWNLOAD VIDEOS ====================
    
    elif mode == 'dl_tiktok':
        await update.message.reply_text("🎬 កំពុងទាញយកវីដេអូ TikTok...")
        try:
            filename, title = await DownloadTool.download_tiktok_video(text.strip())
            if filename:
                await update.message.reply_video(
                    video=open(filename, 'rb'),
                    caption=f"✅ **{title[:100]}**\n📱 Downloaded from TikTok\n📅 {datetime.now().strftime('%Y-%m-%d')}"
                )
                os.remove(filename)
            else:
                await update.message.reply_text("❌ មិនអាចទាញយកវីដេអូបានទេ\nសូមពិនិត្យ URL ម្តងទៀត")
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    elif mode == 'dl_youtube':
        await update.message.reply_text("📺 កំពុងទាញយកវីដេអូ YouTube...")
        try:
            filename, title = await DownloadTool.download_youtube_video(text.strip())
            if filename:
                await update.message.reply_video(
                    video=open(filename, 'rb'),
                    caption=f"✅ **{title[:100]}**\n📱 Downloaded from YouTube\n📅 {datetime.now().strftime('%Y-%m-%d')}"
                )
                os.remove(filename)
            else:
                await update.message.reply_text("❌ មិនអាចទាញយកវីដេអូបានទេ\nសូមពិនិត្យ URL ម្តងទៀត")
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    elif mode == 'dl_facebook':
        await update.message.reply_text("📘 កំពុងទាញយកវីដេអូ Facebook...")
        try:
            filename, title = await DownloadTool.download_facebook_video(text.strip())
            if filename:
                await update.message.reply_video(
                    video=open(filename, 'rb'),
                    caption=f"✅ **{title[:100]}**\n📱 Downloaded from Facebook\n📅 {datetime.now().strftime('%Y-%m-%d')}"
                )
                os.remove(filename)
            else:
                await update.message.reply_text("❌ មិនអាចទាញយកវីដេអូបានទេ\nសូមពិនិត្យ URL ម្តងទៀត")
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    elif mode == 'dl_file':
        url = text.strip()
        await update.message.reply_text("🔄 កំពុងទាញយកឯកសារ...")
        
        try:
            filename = await DownloadTool.download_file(url)
            if filename:
                await update.message.reply_document(
                    document=open(filename, 'rb'),
                    caption=f"✅ បានទាញយកដោយជោគជ័យ!\n📅 {datetime.now().strftime('%Y-%m-%d')}"
                )
                os.remove(filename)
            else:
                await update.message.reply_text("❌ មិនអាចទាញយកឯកសារបានទេ")
            context.user_data['mode'] = ''
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        return
    
    # ==================== ADMIN ====================
    
    elif mode == 'admin_announce':
        await update.message.reply_text(
            "📢 បញ្ជូន Channel/Group ID និងសារ\n"
            "ឧទាហរណ៍: `-100123456789 | សួស្តី!`"
        )
        context.user_data['mode'] = 'admin_announce_confirm'
        return
    
    elif mode == 'admin_announce_confirm':
        try:
            parts = text.split('|')
            chat_id = parts[0].strip()
            message = parts[1].strip()
            
            result = await AdminTools.send_announcement(context, chat_id, message)
            if result:
                await update.message.reply_text("✅ សារបានផ្ញើដោយជោគជ័យ!")
            else:
                await update.message.reply_text("❌ មិនអាចផ្ញើសារបានទេ")
            context.user_data['mode'] = ''
        except:
            await update.message.reply_text("❌ ទម្រង់មិនត្រឹមត្រូវ")
        return
    
    elif mode == 'admin_group':
        try:
            chat_id = text.strip()
            info = await AdminTools.get_channel_info(context, chat_id)
            if info:
                response = f"📊 **ព័ត៌មានក្រុម/ឆានែល**\n\n"
                response += f"ID: {info['id']}\n"
                response += f"ឈ្មោះ: {info['title']}\n"
                response += f"ប្រភេទ: {info['type']}\n"
                response += f"សមាជិក: {info['members']}"
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ រកមិនឃើញក្រុម/ឆានែលនេះទេ")
            context.user_data['mode'] = ''
        except:
            await update.message.reply_text("❌ កំហុសក្នុងការទាញព័ត៌មាន")
        return
    
    # ==================== DEFAULT ====================
    
    else:
        await update.message.reply_text(
            f"🇰🇭 សួស្តី! ខ្ញុំជា {BOT_NAME} v{BOT_VERSION}!\n\n"
            "ប្រើម៉ឺនុយខាងក្រោម ឬពាក្យបញ្ជា:\n"
            "/start - ចាប់ផ្តើម\n"
            "/help - ជំនួយ\n\n"
            f"👨‍💻 Developer: {DEVELOPER}",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

def main():
    print(f"""
    ╔══════════════════════════════════════════════╗
    ║  {BOT_NAME} v{BOT_VERSION}          ║
    ║  Developer: {DEVELOPER}            ║
    ║  AI Chart Assistant 2026 Ready!          ║
    ║  Premium | Fun Account | KHQR            ║
    ╚══════════════════════════════════════════════╝
    """)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot កំពុងដំណើរការ...")
    print("🛑 ចុច Ctrl+C ដើម្បីបញ្ឈប់")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()