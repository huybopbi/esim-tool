#!/usr/bin/env python3
"""
Test script cho các công cụ eSIM
"""

from esim_tools import esim_tools

def test_esim_tools():
    """Test các công cụ eSIM"""
    print("🧪 TESTING eSIM TOOLS")
    print("=" * 50)
    
    # Test 1: Validate SM-DP+ address
    print("\n1️⃣ Test validate SM-DP+ address:")
    test_addresses = [
        "rsp.truphone.com",
        "invalid-address",
        "esim.example.com",
        ""
    ]
    
    for addr in test_addresses:
        is_valid, message = esim_tools.validate_sm_dp_address(addr)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {addr or '(empty)'}: {message}")
    
    # Test 2: Create iPhone install link
    print("\n2️⃣ Test create iPhone install link:")
    link = esim_tools.create_iphone_install_link("rsp.truphone.com", "TEST123")
    print(f"   ✅ Link created: {link}")
    
    # Test extract SM-DP+ from LPA
    print("\n3️⃣ Test extract SM-DP+ from LPA:")
    lpa_data = "LPA:1$rsp.truphone.com$TEST123"
    result = esim_tools.extract_sm_dp_and_activation(lpa_data)
    print(f"   ✅ SM-DP+: {result['sm_dp_address']}")
    print(f"   ✅ Activation: {result['activation_code']}")
    print(f"   ✅ Format: {result['format_type']}")
    
    # Test 4: iPhone compatibility
    print("\n4️⃣ Test iPhone compatibility:")
    test_models = ["iPhone 15", "iPhone X", "iPhone 12 Pro"]
    for model in test_models:
        is_compatible, message = esim_tools.check_iphone_compatibility(model)
        status = "✅" if is_compatible else "❌"
        print(f"   {status} {model}: {message}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_esim_tools() 