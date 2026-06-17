import re
import urllib.parse
import qrcode
import base64
import unicodedata
from io import BytesIO
from PIL import Image
from typing import Dict, Tuple
import cv2
import numpy as np

# Try to import pyzbar (optional dependency)
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except (ImportError, FileNotFoundError) as e:
    # Không print warning vì có thể gây lỗi encoding trên Windows
    PYZBAR_AVAILABLE = False
    pyzbar = None

# Danh sách thiết bị hỗ trợ eSIM
IPHONE_ESIM_MODELS = [
    "iPhone XS", "iPhone XS Max", "iPhone XR",
    "iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15",
    "iPhone SE"
]

ANDROID_ESIM_BRANDS = {
    "Samsung": ["Galaxy S20", "Galaxy S21", "Galaxy S22", "Galaxy S23", "Galaxy Z"],
    "Google": ["Pixel 3", "Pixel 4", "Pixel 5", "Pixel 6", "Pixel 7", "Pixel 8"],
    "OnePlus": ["8", "9", "10", "11"]
}

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
                
                # Don't treat URL as SM-DP+ address - return empty to trigger image download
                result['format_type'] = 'URL'
                # result['sm_dp_address'] = qr_data  # Removed - let caller handle URL
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
    
    def _normalize_bulk_label(self, label: str) -> str:
        """Chuẩn hóa nhãn bulk để nhận cả activecode/Activation Code/mã kích hoạt."""
        normalized = unicodedata.normalize('NFKD', label or '')
        ascii_text = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
        return re.sub(r'[^a-z0-9]+', '', ascii_text.lower())

    def _classify_bulk_label(self, label: str) -> str:
        normalized = self._normalize_bulk_label(label)
        activation_labels = {
            'activationcode', 'activation', 'activecode', 'active',
            'actcode', 'code', 'matchingid', 'matchingcode', 'qrcode',
            'makichhoat', 'ma',
        }
        iccid_labels = {
            'iccid', 'iccidnumber', 'iccidno', 'iccidnum',
            'iccidcode', 'iccidid', 'iccidso', 'iccidma',
            'iccidseri', 'iccidserial', 'iccidmang', 'iccidn',
            'iccidm', 'icc', 'sim', 'simnumber', 'simno', 'simserial',
        }
        sm_dp_labels = {
            'smdp', 'smdpaddress', 'smdpplus', 'smdpserver',
            'smdpaddr', 'smdpurl', 'address', 'server',
        }

        if normalized in activation_labels:
            return 'activation_code'
        if normalized in iccid_labels:
            return 'iccid'
        if normalized in sm_dp_labels:
            return 'sm_dp_address'
        return ''

    def _looks_like_iccid(self, value: str) -> bool:
        compact = re.sub(r'\s+', '', value or '')
        return compact.isdigit() and 10 <= len(compact) <= 22

    def _looks_like_activation_code(self, value: str) -> bool:
        value = (value or '').strip()
        if not value or value.upper().startswith('LPA:') or value.startswith(('http://', 'https://')):
            return False
        if self._looks_like_iccid(value):
            return False
        if '.' in value and re.match(r'^[a-zA-Z0-9.-]+$', value):
            return False
        return bool(re.search(r'[A-Za-z]', value))

    def _parse_bulk_line(self, line: str) -> Tuple[str, str]:
        """Trả về (field_name, value) cho một dòng bulk nếu nhận diện được."""
        line = (line or '').strip()
        if not line:
            return '', ''

        if line.upper().startswith('LPA:'):
            return 'lpa_string', line

        # Nhận "Nhãn: Giá trị", "Nhãn = Giá trị", "Nhãn - Giá trị".
        match = re.match(r'^([^:：=\t]+?)\s*(?:[:：=]|\s+-\s+)\s*(.+)$', line)
        if match:
            field = self._classify_bulk_label(match.group(1).strip())
            value = match.group(2).strip()
            if field and value:
                return field, value

        # Nhận "activecode CODE" / "activationcode CODE" không có dấu phân cách.
        prefix_match = re.match(
            r'^(activation\s*code|activationcode|active\s*code|activecode|act\s*code|actcode|matching\s*id|matchingid|ma\s*kich\s*hoat|mã\s*kích\s*hoạt|iccid|icc\s*id|smdp|sm[-\s]*dp\+?)\s+(.+)$',
            line,
            flags=re.IGNORECASE,
        )
        if prefix_match:
            field = self._classify_bulk_label(prefix_match.group(1).strip())
            value = prefix_match.group(2).strip()
            if field and value:
                return field, value

        # Dòng không nhãn: nhận ICCID số dài, domain SM-DP+, hoặc activation code.
        if self._looks_like_iccid(line):
            return 'iccid', re.sub(r'\s+', '', line)

        if '.' in line and re.match(r'^[a-zA-Z0-9.-]+$', line):
            return 'sm_dp_address', line

        if self._looks_like_activation_code(line):
            return 'activation_code', line

        return '', ''

    def _split_bulk_blocks(self, text: str) -> list:
        """Tách bulk input linh hoạt, kể cả khi người dùng không chèn dòng trống."""
        blocks = []
        current = []
        current_fields = set()

        def flush():
            nonlocal current, current_fields
            if current:
                blocks.append('\n'.join(current).strip())
                current = []
                current_fields = set()

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                flush()
                continue

            field, _ = self._parse_bulk_line(line)

            # Nếu block hiện tại đã có activation/LPA rồi mà gặp eSIM mới,
            # tự tách block để không cần dòng trống giữa các eSIM.
            starts_new_entry = (
                field == 'lpa_string' and current_fields
            ) or (
                field == 'activation_code' and (
                    'activation_code' in current_fields or 'lpa_string' in current_fields
                )
            )
            if starts_new_entry:
                flush()

            current.append(line)
            if field:
                current_fields.add(field)

        flush()
        return blocks

    def _parse_block_fields(self, block: str) -> Dict[str, str]:
        """Tách các trường có nhãn trong một block (Activation Code / ICCID / SM-DP+ / LPA)."""
        fields: Dict[str, str] = {}

        for raw_line in block.splitlines():
            field, value = self._parse_bulk_line(raw_line)
            if field and value:
                fields[field] = value

        return fields

    def parse_bulk_esim_input(
        self,
        text: str,
        default_sm_dp_address: str = "",
    ) -> Tuple[list, list]:
        """Phân tích danh sách eSIM dán hàng loạt.

        Mỗi eSIM là một block, các block cách nhau bằng dòng trống. Mỗi block có
        thể chứa các trường ``Activation Code``, ``ICCID``, ``SM-DP+`` hoặc một
        dòng ``LPA:`` thô. SM-DP+ riêng của block (hoặc LPA thô) sẽ ghi đè
        ``default_sm_dp_address``.

        Trả về ``(entries, errors)`` trong đó mỗi entry là dict gồm
        ``sm_dp_address``, ``activation_code``, ``iccid``, ``lpa_string`` và mỗi
        error là dict gồm ``block`` và ``reason``.
        """
        entries: list = []
        errors: list = []

        if not text or not text.strip():
            return entries, errors

        default_sm_dp_address = (default_sm_dp_address or "").strip()

        raw_blocks = self._split_bulk_blocks(text.strip())

        for raw in raw_blocks:
            block = raw.strip()
            if not block:
                continue

            fields = self._parse_block_fields(block)
            lpa = fields.get('lpa_string', '')
            iccid = fields.get('iccid', '')

            # Ưu tiên dòng LPA thô nếu có
            if lpa:
                is_valid, message = self.validate_lpa_string(lpa)
                if not is_valid:
                    errors.append({'block': block, 'reason': message})
                    continue
                analysis = self.extract_sm_dp_and_activation(lpa)
                entries.append({
                    'sm_dp_address': analysis['sm_dp_address'],
                    'activation_code': analysis['activation_code'],
                    'iccid': iccid,
                    'lpa_string': lpa.strip(),
                })
                continue

            sm_dp = fields.get('sm_dp_address') or default_sm_dp_address
            activation_code = fields.get('activation_code', '')

            if not sm_dp:
                errors.append({'block': block, 'reason': 'Thiếu SM-DP+ address'})
                continue

            is_valid, message = self.validate_sm_dp_address(sm_dp)
            if not is_valid:
                errors.append({'block': block, 'reason': message})
                continue

            if not activation_code:
                errors.append({'block': block, 'reason': 'Thiếu Activation Code'})
                continue

            lpa_string = f"LPA:1${sm_dp}${activation_code}"
            entries.append({
                'sm_dp_address': sm_dp,
                'activation_code': activation_code,
                'iccid': iccid,
                'lpa_string': lpa_string,
            })

        return entries, errors

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
            
            # Method 1: Try pyzbar first (faster and more reliable)
            if PYZBAR_AVAILABLE:
                try:
                    # Convert to grayscale for better QR detection
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Decode QR codes
                    qr_codes = pyzbar.decode(gray)
                    
                    if not qr_codes:
                        # Thử với ảnh gốc nếu grayscale không work
                        qr_codes = pyzbar.decode(img)
                    
                    if qr_codes:
                        # Lấy QR code đầu tiên
                        qr_data = qr_codes[0].data.decode('utf-8')
                        return qr_data
                except Exception as e:
                    print(f"⚠️ pyzbar failed: {e}, trying OpenCV fallback...")
            
            # Method 2: Fallback to OpenCV QRCodeDetector
            qr_detector = cv2.QRCodeDetector()
            
            # Try with original image
            data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
            
            if data:
                return data
            
            # Try with grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            data, bbox, straight_qrcode = qr_detector.detectAndDecode(gray)
            
            if data:
                return data
            
            # Try with enhanced contrast
            enhanced = cv2.equalizeHist(gray)
            data, bbox, straight_qrcode = qr_detector.detectAndDecode(enhanced)
            
            if data:
                return data
            
            raise Exception("Không tìm thấy QR code trong ảnh")
            
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

# Export availability flag
__all__ = ['esim_tools', 'PYZBAR_AVAILABLE'] 