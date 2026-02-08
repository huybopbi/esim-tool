"""
SimplifyTrip API Client
Module để gọi API SimplifyTrip check thông tin eSIM theo ICCID
Hỗ trợ auto login và refresh token khi hết hạn
Lưu cookies vào file để không cần login lại khi restart bot
"""

import requests
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import time

from config import (
    SIMPLIFYTRIP_API_URL, 
    SIMPLIFYTRIP_EMAIL,
    SIMPLIFYTRIP_PASSWORD
)

logger = logging.getLogger(__name__)

# File lưu cookies
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'simplifytrip_cookies.json')


class SimplifyTripAPI:
    """Client để gọi SimplifyTrip API với auto refresh token"""
    
    BASE_URL = "https://api.simplifytrip.com/api/v1"
    
    def __init__(self):
        self.api_url = SIMPLIFYTRIP_API_URL
        self.timeout = 15
        
        # Session để giữ cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Origin': 'https://simplifytrip.com',
            'Referer': 'https://simplifytrip.com/',
        })
        
        # Token info
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.csrf_token = None
        
        # Lock để tránh race condition khi refresh token
        self._token_lock = threading.Lock()
        
        # Load cookies từ file trước, nếu không có thì load từ config
        self._load_cookies()
    
    def _load_cookies(self):
        """Load cookies từ file, nếu không có thì load từ config.py"""
        # Thử load từ file trước
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                
                # Load cookies vào session
                cookies = saved_data.get('cookies', {})
                for name, value in cookies.items():
                    if value:  # Chỉ set nếu có giá trị
                        self.session.cookies.set(name, value, domain='.simplifytrip.com')
                
                # Load tokens
                self.access_token = saved_data.get('access_token')
                self.refresh_token = saved_data.get('refresh_token')
                self.token_expires_at = saved_data.get('token_expires_at')
                self.csrf_token = saved_data.get('csrf_token')
                
                logger.info("Loaded cookies from file")
                return
            except Exception as e:
                logger.warning(f"Could not load cookies from file: {e}")
        
        # Không có file cookies, sẽ login khi cần
        pass
    
    def _save_cookies(self):
        """Lưu cookies vào file"""
        try:
            # Thu thập cookies quan trọng
            cookies = {
                '__Secure-SIM.JT': self.access_token,
                '__Secure-SIM.RFT': self.refresh_token,
                'cf_clearance': self.session.cookies.get('cf_clearance'),
                '__Host-SIM.CSRF': self.csrf_token,
                'SIM.LC': 'true',
            }
            
            saved_data = {
                'cookies': cookies,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_expires_at': self.token_expires_at,
                'csrf_token': self.csrf_token,
                'saved_at': time.time()
            }
            
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(saved_data, f, indent=2)
            
            logger.info("Saved cookies to file")
        except Exception as e:
            logger.warning(f"Could not save cookies to file: {e}")
    
    def _get_csrf_token(self) -> Optional[str]:
        """Lấy CSRF token từ server"""
        try:
            url = f"{self.BASE_URL}/csrf-token"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.csrf_token = data.get('csrfToken')
                return self.csrf_token
            return None
        except:
            return None
    
    def login(self, email: str = None, password: str = None) -> bool:
        """
        Đăng nhập vào SimplifyTrip
        
        Args:
            email: Email đăng nhập (mặc định lấy từ config)
            password: Mật khẩu (mặc định lấy từ config)
            
        Returns:
            True nếu đăng nhập thành công
        """
        email = email or SIMPLIFYTRIP_EMAIL
        password = password or SIMPLIFYTRIP_PASSWORD
        
        if not email or not password:
            logger.error("Missing login credentials in config.py")
            return False
        
        try:
            # Lấy CSRF token trước
            self._get_csrf_token()
            
            # Gọi API login
            url = f"{self.BASE_URL}/auth/login"
            payload = {"email": email, "password": password}
            
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            response = self.session.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Extract tokens từ response
                backend_tokens = data.get('backendTokens', {})
                self.access_token = backend_tokens.get('accessToken')
                self.refresh_token = backend_tokens.get('refreshToken')
                expires_in = backend_tokens.get('expiresIn', 3600000)  # Default 1 hour
                
                # Tính thời gian hết hạn (trừ 5 phút để refresh sớm)
                self.token_expires_at = time.time() + (expires_in / 1000) - 300
                
                # Extract tokens từ cookies
                for cookie in self.session.cookies:
                    if cookie.name == '__Secure-SIM.JT':
                        self.access_token = cookie.value
                    elif cookie.name == '__Secure-SIM.RFT':
                        self.refresh_token = cookie.value
                
                # Lưu cookies vào file
                self._save_cookies()
                
                logger.info(f"Login successful: {email}")
                return True
            else:
                logger.error(f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Refresh access token sử dụng refresh token
        
        Returns:
            True nếu refresh thành công
        """
        if not self.refresh_token:
            logger.warning("No refresh token, need to login again")
            return self.login()
        
        try:
            url = f"{self.BASE_URL}/auth/refresh"
            
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            # Gửi refresh token trong body hoặc cookie
            response = self.session.post(url, headers=headers, timeout=15)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Extract new tokens
                backend_tokens = data.get('backendTokens', {})
                if backend_tokens:
                    self.access_token = backend_tokens.get('accessToken', self.access_token)
                    self.refresh_token = backend_tokens.get('refreshToken', self.refresh_token)
                    expires_in = backend_tokens.get('expiresIn', 3600000)
                    self.token_expires_at = time.time() + (expires_in / 1000) - 300
                
                # Update từ cookies
                for cookie in self.session.cookies:
                    if cookie.name == '__Secure-SIM.JT':
                        self.access_token = cookie.value
                    elif cookie.name == '__Secure-SIM.RFT':
                        self.refresh_token = cookie.value
                
                # Lưu cookies vào file
                self._save_cookies()
                
                logger.info("Token refreshed successfully")
                return True
            else:
                # Refresh thất bại, thử đăng nhập lại
                logger.warning(f"Refresh token failed ({response.status_code}), logging in again...")
                return self.login()
                
        except Exception as e:
            logger.error(f"Refresh token error: {e}")
            return self.login()
    
    def _ensure_valid_token(self) -> bool:
        """Đảm bảo có token hợp lệ trước khi gọi API"""
        with self._token_lock:
            # Kiểm tra token có hết hạn chưa
            if self.token_expires_at and time.time() >= self.token_expires_at:
                logger.info("Token expiring soon, refreshing...")
                return self.refresh_access_token()
            
            # Nếu chưa có token, thử đăng nhập
            if not self.access_token:
                logger.info("No token, logging in...")
                return self.login()
            
            return True
    
    def check_iccid(self, iccid: str) -> Dict[str, Any]:
        """
        Check thông tin eSIM theo ICCID
        
        Args:
            iccid: Mã ICCID của eSIM (thường 19-20 số)
            
        Returns:
            Dict chứa thông tin eSIM hoặc thông báo lỗi
        """
        # Validate ICCID
        iccid = iccid.strip()
        if not iccid.isdigit():
            return {"success": False, "error": "ICCID chỉ được chứa số"}
        
        if len(iccid) < 18 or len(iccid) > 22:
            return {"success": False, "error": "ICCID phải có từ 18-22 số"}
        
        # Đảm bảo có token hợp lệ
        if not self._ensure_valid_token():
            return {"success": False, "error": "Không thể xác thực. Vui lòng kiểm tra thông tin đăng nhập trong config.py"}
        
        try:
            url = f"{self.api_url}/{iccid}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            elif response.status_code == 401 or response.status_code == 403:
                # Token hết hạn, thử refresh và gọi lại
                logger.warning("Token invalid, refreshing...")
                if self.refresh_access_token():
                    # Thử lại request
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        return {"success": True, "data": response.json()}
                
                return {"success": False, "error": "Token đã hết hạn và không thể refresh. Vui lòng kiểm tra thông tin đăng nhập."}
            elif response.status_code == 404:
                return {"success": False, "error": "Không tìm thấy eSIM với ICCID này"}
            else:
                return {"success": False, "error": f"Lỗi API: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout - API không phản hồi"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Lỗi kết nối: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Lỗi không xác định: {str(e)}"}
    
    def format_esim_info(self, data: Dict[str, Any]) -> str:
        """
        Format thông tin eSIM thành message đẹp cho Telegram
        
        Args:
            data: Dữ liệu từ API
            
        Returns:
            String đã format cho Telegram (Markdown)
        """
        # Thông tin cơ bản
        name = data.get('name', 'N/A')
        plan_status = data.get('planStatus', 'N/A')
        plan_type = data.get('planType', 'N/A')
        point_contact_type = data.get('pointContactType', 'N/A')
        
        # Thời gian
        plan_start = data.get('planStartTime', 'N/A')
        plan_end = data.get('planEndTime', 'N/A')
        total_days = data.get('totalDays', 'N/A')
        remaining_days = data.get('remainingDays', 'N/A')
        
        # Dung lượng (đơn vị KB)
        total_traffic_kb = int(data.get('totalTraffic', 0))
        remaining_traffic_kb = int(data.get('remainingTraffic', 0))
        used_traffic_kb = int(data.get('usedTraffic', 0))
        high_flow_kb = int(data.get('highFlowSize', 0))
        
        # Convert to MB/GB
        def format_traffic(kb: int) -> str:
            if kb >= 1024 * 1024:
                return f"{kb / (1024 * 1024):.2f} GB"
            elif kb >= 1024:
                return f"{kb / 1024:.2f} MB"
            else:
                return f"{kb} KB"
        
        # Order info
        order_id = data.get('orderId', 'N/A')
        vendor_order_id = data.get('vendorOrderId', 'N/A')
        
        # Activity logs - lấy trạng thái mới nhất
        activity_logs = data.get('activityLogs', [])
        latest_status = "N/A"
        eid = "N/A"
        if activity_logs:
            latest_log = activity_logs[0]
            latest_status = latest_log.get('status', 'N/A')
            eid = latest_log.get('eid', 'N/A') or 'N/A'
        
        # Status emoji
        status_emoji = "🟢" if plan_status == "Đang sử dụng" else "🟡" if "chưa" in plan_status.lower() else "🔴"
        
        # Build message
        message = f"""📱 **THÔNG TIN eSIM**

{status_emoji} **Trạng thái:** {plan_status}
📋 **Gói cước:** {name}
📦 **Loại gói:** {point_contact_type}

⏰ **THỜI GIAN**
• Bắt đầu: {plan_start}
• Kết thúc: {plan_end}
• Tổng: {total_days} ngày
• Còn lại: **{remaining_days} ngày**

📊 **DUNG LƯỢNG**
• Tổng: {format_traffic(total_traffic_kb)}
• Đã dùng: {format_traffic(used_traffic_kb)}
• Còn lại: **{format_traffic(remaining_traffic_kb)}**
• Tốc độ cao: {format_traffic(high_flow_kb)}/ngày

🔖 **THÔNG TIN KHÁC**
• Order ID: `{order_id}`
• Vendor ID: `{vendor_order_id}`
• EID: `{eid}`"""

        # Thêm 3 activity logs gần nhất
        if activity_logs:
            message += "\n\n📝 **LỊCH SỬ HOẠT ĐỘNG (3 gần nhất)**"
            for log in activity_logs[:3]:
                log_status = log.get('status', 'N/A')
                log_time = log.get('recordTime', 'N/A')
                # Emoji theo trạng thái
                if 'kích hoạt' in log_status.lower():
                    log_emoji = "✅"
                elif 'cài đặt' in log_status.lower():
                    log_emoji = "📲"
                elif 'tải xuống' in log_status.lower():
                    log_emoji = "⬇️"
                elif 'chưa' in log_status.lower():
                    log_emoji = "⏳"
                else:
                    log_emoji = "📌"
                message += f"\n{log_emoji} {log_time} - {log_status}"

        # Thêm lịch sử sử dụng nếu có
        usage_list = data.get('usageInfoList', [])
        if usage_list:
            message += "\n\n📈 **LỊCH SỬ SỬ DỤNG (3 ngày gần nhất)**"
            for usage in usage_list[-3:]:
                date_str = usage.get('usedDate', '')
                if date_str:
                    # Format date từ 20260129 thành 29/01/2026
                    try:
                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                        formatted_date = date_obj.strftime('%d/%m/%Y')
                    except:
                        formatted_date = date_str
                    
                    usage_kb = int(usage.get('usageAmt', 0))
                    message += f"\n• {formatted_date}: {format_traffic(usage_kb)}"
        
        return message


# Singleton instance
simplifytrip_api = SimplifyTripAPI()
