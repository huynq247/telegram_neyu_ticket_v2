"""
Multi-Destination Configuration for Ticket System
Cấu hình cho hệ thống ticket đa điểm đến
"""

# Country Configuration - Cấu hình các quốc gia
COUNTRY_CONFIG = {
    'Vietnam': {
        'code': 'VN',           # Mã quốc gia ISO
        'table': 'helpdesk_ticket',  # Bảng hiện tại (có thể tách sau)
        'prefix': 'VN',         # Prefix cho ticket number
        'name_template': 'From Telegram Vietnam',
        'description_template': '{description}',
        'sequence': 'helpdesk_ticket_id_seq',  # Sequence hiện tại
        'team_id': 4,           # Team ID mặc định
        'stage_id': 1           # Stage ID mặc định
    },
    'Thailand': {
        'code': 'TH',
        'table': 'helpdesk_ticket_thailand',  # Bảng riêng cho Thailand
        'prefix': 'TH', 
        'name_template': 'From Telegram Thailand',
        'description_template': '{description}',
        'sequence': 'helpdesk_ticket_thailand_seq',
        'team_id': 5,           # Thailand team (correct mapping)
        'stage_id': 1
    },
    'India': {
        'code': 'IN',
        'table': 'helpdesk_ticket_india',     # Bảng riêng cho India
        'prefix': 'IN',
        'name_template': 'From Telegram India', 
        'description_template': '{description}',
        'sequence': 'helpdesk_ticket_india_seq',
        'team_id': 9,           # India team (correct mapping)
        'stage_id': 1
    },
    'Philippines': {
        'code': 'PH',
        'table': 'helpdesk_ticket_philippines',
        'prefix': 'PH',
        'name_template': 'From Telegram Philippines',
        'description_template': '{description}',
        'sequence': 'helpdesk_ticket_philippines_seq', 
        'team_id': 8,           # Philippines team
        'stage_id': 1
    },
    'Malaysia': {
        'code': 'MY',
        'table': 'helpdesk_ticket_malaysia',
        'prefix': 'MY',
        'name_template': 'From Telegram Malaysia',
        'description_template': '{description}',
        'sequence': 'helpdesk_ticket_malaysia_seq',
        'team_id': 6,           # Malaysia team
        'stage_id': 1
    },
    'Indonesia': {
        'code': 'ID',
        'table': 'helpdesk_ticket_indonesia',
        'prefix': 'ID',
        'name_template': 'From Telegram Indonesia',
        'description_template': '{description}',
        'sequence': 'helpdesk_ticket_indonesia_seq', 
        'team_id': 7,           # Indonesia team (Team 6)
        'stage_id': 1
    }
}

# Mapping display names to country codes
COUNTRY_DISPLAY_NAMES = {
    'Việt Nam': 'Vietnam',
    'Vietnam': 'Vietnam',
    'Thái Lan': 'Thailand', 
    'Thailand': 'Thailand',
    'Ấn Độ': 'India',
    'India': 'India',
    'Philippines': 'Philippines',
    'Phi-líp-pin': 'Philippines',
    'Malaysia': 'Malaysia',
    'Mã Lai': 'Malaysia',
    'Indonesia': 'Indonesia',
    'In-đô-nê-xi-a': 'Indonesia'
}

def get_country_config(country_name: str) -> dict:
    """
    Lấy cấu hình cho quốc gia
    
    Args:
        country_name: Tên quốc gia (Vietnam, Thailand, India, etc.)
        
    Returns:
        Dictionary chứa cấu hình quốc gia
        
    Raises:
        ValueError: Nếu quốc gia không được hỗ trợ
    """
    # Normalize country name
    normalized_name = COUNTRY_DISPLAY_NAMES.get(country_name, country_name)
    
    if normalized_name not in COUNTRY_CONFIG:
        supported_countries = list(COUNTRY_CONFIG.keys())
        raise ValueError(f"Quốc gia '{country_name}' không được hỗ trợ. Các quốc gia hỗ trợ: {supported_countries}")
    
    return COUNTRY_CONFIG[normalized_name]

def get_supported_countries() -> list:
    """Trả về danh sách các quốc gia được hỗ trợ"""
    return list(COUNTRY_CONFIG.keys())

def get_country_display_options() -> list:
    """Trả về danh sách tùy chọn hiển thị cho user"""
    return list(COUNTRY_DISPLAY_NAMES.keys())

# Validation function
def validate_country_config():
    """Kiểm tra tính hợp lệ của cấu hình"""
    required_fields = ['code', 'table', 'prefix', 'name_template', 'sequence']
    
    for country, config in COUNTRY_CONFIG.items():
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Thiếu field '{field}' trong cấu hình cho {country}")
        
        # Validate prefix length (should be 2 characters)
        if len(config['prefix']) != 2:
            raise ValueError(f"Prefix '{config['prefix']}' cho {country} phải có 2 ký tự")

if __name__ == "__main__":
    # Test configuration
    validate_country_config()
    print("✅ Configuration validation passed")
    
    # Test country lookup
    for display_name in COUNTRY_DISPLAY_NAMES:
        try:
            config = get_country_config(display_name)
            print(f"✅ {display_name} → {config['code']} → {config['prefix']}XXXXX")
        except ValueError as e:
            print(f"❌ {display_name}: {e}")