#!/usr/bin/env python3
"""
Test validation function
"""
import sys
import os
sys.path.append('.')

def test_validation():
    # Copy the validation function here for testing
    def _is_valid_ticket_number(text: str) -> bool:
        import re
        
        # Remove whitespace
        text = text.strip()
        
        # If text contains multiple words or is very long, likely a comment
        if ' ' in text or len(text) > 25:
            return False
        
        # If text is too short, also invalid
        if len(text) < 3:
            return False
        
        # Check for common comment indicators
        comment_indicators = [
            'this', 'that', 'please', 'help', 'issue', 'problem', 
            'bug', 'error', 'fix', 'need', 'want', 'can', 'could',
            'should', 'would', 'have', 'has', 'will', 'was', 'were',
            'hello', 'hi', 'thanks', 'thank', 'sorry'
        ]
        
        text_lower = text.lower()
        for indicator in comment_indicators:
            if indicator in text_lower:
                return False
        
        # Check if text contains typical ticket number patterns
        # Examples: TH220925757, VN00027, IN00602
        ticket_patterns = [
            r'^[A-Z]{2}\d{8,}$',  # TH220925757 format
            r'^[A-Z]{2}\d{5,7}$', # VN00027, IN00602 format  
            r'^[A-Z]{1,3}\d{3,}$', # General pattern with letters + numbers
            r'^\d{4,}$',          # Pure numbers (some systems use this)
        ]
        
        for pattern in ticket_patterns:
            if re.match(pattern, text.upper()):
                return True
        
        # If none of the patterns match and it doesn't look like a comment,
        # still give it a chance (could be a different ticket format)
        # But if it has special characters or looks like natural language, reject
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', text):
            return False
        
        # If it's all letters (no numbers), likely not a ticket number
        if text.isalpha():
            return False
            
        return True
    
    # Test cases
    test_cases = [
        ("TH220925757", True),      # Valid ticket
        ("VN00027", True),          # Valid ticket
        ("IN00602", True),          # Valid ticket
        ("adsfadsf", False),        # Invalid - random text
        ("this is a comment", False), # Invalid - sentence
        ("please help me", False),   # Invalid - sentence with keywords
        ("123", False),             # Invalid - too short
        ("", False),                # Invalid - empty
        ("ABC", False),             # Invalid - only letters
        ("12345", True),            # Valid - numbers only
        ("TEST123", True),          # Valid - letters + numbers
    ]
    
    print("Testing validation function:")
    print("=" * 50)
    
    for test_input, expected in test_cases:
        result = _is_valid_ticket_number(test_input)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | '{test_input}' -> {result} (expected: {expected})")
    
    print("=" * 50)

if __name__ == "__main__":
    test_validation()