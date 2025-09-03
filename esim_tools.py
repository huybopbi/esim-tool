import re
import urllib.parse
import qrcode
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, Tuple
import cv2
import numpy as np
from pyzbar import pyzbar

from config import IPHONE_ESIM_MODELS, ANDROID_ESIM_BRANDS

class eSIMTools:
    def __init__(self):
        pass
    
    def create_iphone_install_link(self, sm_dp_address: str, activation_code: str = None) -> str:
        """Tạo link cài eSIM nhanh cho iPhone từ SM-DP+ address và activation code"""
        try:
            # Tạo LPA string
            if activation_code and activation_code.strip():
                lpa_string = f"LPA:1${sm_dp_address}${activation_code}"
            else:
                lpa_string = f"LPA:1${sm_dp_address}$"
            
            # Tạo URL scheme cho iPhone (Apple Universal Link không cần encode : và $)
            install_link = f"https://esimsetup.apple.com/esim_qrcode_provisioning?carddata={lpa_string}"
            
            return install_link
        except Exception as e:
            raise Exception(f"Lỗi tạo link cài đặt: {e}")
    
    def create_qr_from_sm_dp(self, sm_dp_address: str, activation_code: str = None) -> Tuple[BytesIO, str]:
        """Tạo QR code từ SM-DP+ address và activation code"""
        try:
            # Tạo LPA string
            if activation_code and activation_code.strip():
                lpa_string = f"LPA:1${sm_dp_address}${activation_code}"
            else:
                lpa_string = f"LPA:1${sm_dp_address}$"
            
            # Tạo QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(lpa_string)
            qr.make(fit=True)
            
            # Tạo hình ảnh
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to BytesIO
            bio = BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            
            return bio, lpa_string
        except Exception as e:
            raise Exception(f"Lỗi tạo QR code: {e}")

    def create_qr_from_lpa(self, lpa_string: str) -> Tuple[BytesIO, str]:
        """Tạo QR code trực tiếp từ LPA string"""
        try:
            # Validate LPA string
            is_valid, message = self.validate_lpa_string(lpa_string)
            if not is_valid:
                raise ValueError(message)

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(lpa_string)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to BytesIO
            bio = BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)

            return bio, lpa_string
        except Exception as e:
            raise Exception(f"Lỗi tạo QR từ LPA string: {e}")
    
    def create_install_link_from_qr(self, qr_data: str) -> str:
        """Tạo link cài đặt từ dữ liệu QR code"""
        try:
            # Kiểm tra và làm sạch dữ liệu
            qr_data = qr_data.strip()
            
            # Nếu đã là LPA format
            if qr_data.startswith('LPA:'):
                return f"https://esimsetup.apple.com/esim_qrcode_provisioning?carddata={qr_data}"
            
            # Nếu là URL
            elif qr_data.startswith('http'):
                return qr_data
            
            # Nếu là SM-DP+ address thuần
            else:
                lpa_string = f"LPA:1${qr_data}$"
                return f"https://esimsetup.apple.com/esim_qrcode_provisioning?carddata={lpa_string}"
                
        except Exception as e:
            raise Exception(f"Lỗi tạo link từ QR: {e}")
    
    def extract_sm_dp_and_activation(self, qr_data: str) -> Dict[str, str]:
        """Tách SM-DP+ address và activation code từ QR data"""
        try:
            qr_data = qr_data.strip()
            result = {
                'sm_dp_address': '',
                'activation_code': '',
                'format_type': 'unknown',
                'original_data': qr_data
            }
            
            # Kiểm tra LPA format: LPA:1$SM-DP+$ACTIVATION_CODE
            lpa_pattern = r'^LPA:1\$([^$]+)\$(.*)$'
            lpa_match = re.match(lpa_pattern, qr_data)
            
            if lpa_match:
                result['sm_dp_address'] = lpa_match.group(1)
                result['activation_code'] = lpa_match.group(2) if lpa_match.group(2) else ''
                result['format_type'] = 'LPA'
                return result
            
            # Kiểm tra URL format
            if qr_data.startswith('http'):
                # Thử extract từ URL parameters
                if 'carddata=' in qr_data:
                    try:
                        parsed_url = urllib.parse.urlparse(qr_data)
                        params = urllib.parse.parse_qs(parsed_url.query)
                        if 'carddata' in params:
                            carddata = urllib.parse.unquote(params['carddata'][0])
                            return self.extract_sm_dp_and_activation(carddata)
                    except:
                        pass
                
                result['format_type'] = 'URL'
                result['sm_dp_address'] = qr_data
                return result
            
            # Kiểm tra nếu là SM-DP+ address thuần
            if '.' in qr_data and len(qr_data) > 10:
                result['sm_dp_address'] = qr_data
                result['format_type'] = 'SM-DP+'
                return result
            
            # Kiểm tra Base64 encoded data
            try:
                decoded = base64.b64decode(qr_data + '==')  # Add padding
                decoded_str = decoded.decode('utf-8')
                if 'LPA:' in decoded_str:
                    return self.extract_sm_dp_and_activation(decoded_str)
            except:
                pass
            
            result['format_type'] = 'unknown'
            return result
            
        except Exception as e:
            return {
                'sm_dp_address': '',
                'activation_code': '',
                'format_type': 'error',
                'error': str(e),
                'original_data': qr_data
            }
    
    def validate_sm_dp_address(self, sm_dp_address: str) -> Tuple[bool, str]:
        """Kiểm tra tính hợp lệ của SM-DP+ address"""
        if not sm_dp_address or not sm_dp_address.strip():
            return False, "SM-DP+ address không được để trống"
        
        sm_dp_address = sm_dp_address.strip()
        
        # Kiểm tra format cơ bản
        if not re.match(r'^[a-zA-Z0-9.-]+$', sm_dp_address):
            return False, "SM-DP+ address chứa ký tự không hợp lệ"
        
        # Kiểm tra có chứa dấu chấm (domain)
        if '.' not in sm_dp_address:
            return False, "SM-DP+ address phải là một domain hợp lệ"
        
        # Kiểm tra độ dài
        if len(sm_dp_address) < 5 or len(sm_dp_address) > 255:
            return False, "SM-DP+ address có độ dài không hợp lệ"
        
        return True, "SM-DP+ address hợp lệ"

    def validate_lpa_string(self, lpa_string: str) -> Tuple[bool, str]:
        """Kiểm tra tính hợp lệ của LPA string."""
        if not lpa_string or not lpa_string.strip():
            return False, "LPA string không được để trống"

        lpa_string = lpa_string.strip()

        # LPA string must start with LPA:1$
        lpa_pattern = r'^LPA:1\$([^$]+)\$(.*)$'
        
        if not re.match(lpa_pattern, lpa_string):
            return False, "LPA string không hợp lệ. Cần có định dạng LPA:1$SMDP_ADDRESS$CODE"

        return True, "LPA string hợp lệ"
    
    def create_detailed_qr_info(self, qr_data: str) -> Dict:
        """Tạo thông tin chi tiết về QR code"""
        try:
            extracted = self.extract_sm_dp_and_activation(qr_data)
            
            info = {
                'original_data': qr_data,
                'format_type': extracted['format_type'],
                'sm_dp_address': extracted['sm_dp_address'],
                'activation_code': extracted['activation_code'],
                'is_valid': False,
                'install_methods': [],
                'notes': []
            }
            
            # Kiểm tra tính hợp lệ
            if extracted['sm_dp_address']:
                is_valid, message = self.validate_sm_dp_address(extracted['sm_dp_address'])
                info['is_valid'] = is_valid
                if not is_valid:
                    info['notes'].append(f"⚠️ {message}")
            
            # Thêm phương thức cài đặt
            if info['is_valid']:
                info['install_methods'].extend([
                    "📱 Quét QR code trực tiếp",
                    "🔗 Sử dụng link cài đặt nhanh",
                    "⌨️ Nhập thủ công SM-DP+ address"
                ])
                
                if extracted['activation_code']:
                    info['notes'].append("✅ Có mã kích hoạt")
                else:
                    info['notes'].append("ℹ️ Không có mã kích hoạt (có thể không cần)")
            
            return info
            
        except Exception as e:
            return {
                'original_data': qr_data,
                'format_type': 'error',
                'error': str(e),
                'is_valid': False
            }
    
    def generate_qr_with_logo(self, esim_data: str, logo_text: str = "eSIM") -> BytesIO:
        """Tạo QR code với logo text"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(esim_data)
            qr.make(fit=True)
            
            # Tạo QR image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to BytesIO
            bio = BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            
            return bio
        except Exception as e:
            raise Exception(f"Lỗi tạo QR với logo: {e}")
    
    def decode_qr_from_image(self, image_data: bytes) -> str:
        """Đọc QR code từ dữ liệu ảnh"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            
            # Decode image
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise Exception("Không thể đọc ảnh")
            
            # Convert to grayscale for better QR detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Decode QR codes
            qr_codes = pyzbar.decode(gray)
            
            if not qr_codes:
                # Thử với ảnh gốc nếu grayscale không work
                qr_codes = pyzbar.decode(img)
            
            if not qr_codes:
                raise Exception("Không tìm thấy QR code trong ảnh")
            
            # Lấy QR code đầu tiên
            qr_data = qr_codes[0].data.decode('utf-8')
            return qr_data
            
        except Exception as e:
            raise Exception(f"Lỗi đọc QR từ ảnh: {e}")
    
    def analyze_qr_image(self, image_data: bytes) -> Dict:
        """Phân tích QR code từ ảnh và trả về thông tin chi tiết"""
        try:
            # Đọc QR data từ ảnh
            qr_data = self.decode_qr_from_image(image_data)
            
            # Phân tích QR data
            analysis = self.create_detailed_qr_info(qr_data)
            
            # Thêm thông tin về việc đọc từ ảnh
            analysis['source'] = 'image'
            analysis['qr_detected'] = True
            
            return analysis
            
        except Exception as e:
            return {
                'source': 'image',
                'qr_detected': False,
                'error': str(e),
                'sm_dp_address': '',
                'activation_code': '',
                'format_type': 'error'
            }
    
    def check_iphone_compatibility(self, model: str) -> Tuple[bool, str]:
        """Kiểm tra iPhone có hỗ trợ eSIM không"""
        model_clean = model.strip().title()
        
        for supported_model in IPHONE_ESIM_MODELS:
            if supported_model.lower() in model_clean.lower():
                return True, f"✅ {model_clean} hỗ trợ eSIM!"
        
        # Kiểm tra các model cũ không hỗ trợ
        old_models = ['iPhone 6', 'iPhone 7', 'iPhone 8', 'iPhone X']
        for old_model in old_models:
            if old_model.lower() in model_clean.lower():
                return False, f"❌ {model_clean} không hỗ trợ eSIM. Cần iPhone XS/XR trở lên."
        
        return False, f"⚠️ Không thể xác định {model_clean}. Vui lòng kiểm tra thủ công trong Cài đặt → Cellular."
    
    def check_android_compatibility(self, brand: str, model: str = None) -> Tuple[bool, str]:
        """Kiểm tra Android có hỗ trợ eSIM không"""
        brand_clean = brand.strip().title()
        
        if brand_clean in ANDROID_ESIM_BRANDS:
            supported_models = ANDROID_ESIM_BRANDS[brand_clean]
            
            if model:
                model_clean = model.strip()
                for supported_model in supported_models:
                    if any(part.lower() in model_clean.lower() for part in supported_model.split()):
                        return True, f"✅ {brand_clean} {model_clean} hỗ trợ eSIM!"
                
                return False, f"❌ {brand_clean} {model_clean} có thể không hỗ trợ eSIM."
            else:
                models_text = ", ".join(supported_models[:3])
                return True, f"✅ {brand_clean} có các model hỗ trợ eSIM: {models_text}..."
        
        return False, f"⚠️ {brand_clean} có ít model hỗ trợ eSIM. Kiểm tra trong Cài đặt → Mạng & Internet → SIM."

# Khởi tạo eSIM tools
esim_tools = eSIMTools() 