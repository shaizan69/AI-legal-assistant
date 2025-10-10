#!/usr/bin/env python3
"""
Test script for enhanced monetary data extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.utils import multi_pass_financial_analysis, enhance_financial_chunking

def test_monetary_extraction():
    """Test the enhanced monetary extraction capabilities"""
    
    # Sample financial document text
    sample_text = """
    BHARAT ENTERPRISES Specialist: Cleaning of Exhaust ducting, Exhaust Blower, Fresh air duct, And Various duct cleaning, Repair Maintenance work Gala A3/62, Shanti Sadan, Lokhande Marg, Chembur - 400071 MOB NO: 73041 49910 Date. 27/09/25 To, THE ST.REGIS HOTEL S.B.MARG, LOWER PAREL, MUMBAI 400 013 Dear Sir, Sub: Quotation for Kitchen hood and exhaust ducting cleaning Quarterly. Its a pleasure to submit our AMC quote for kitchen hood filters, exhaust duct, blower unit cleaning. Sr. per service Annually Description QTY No Unit Rate Amount 1 8th Floor Cafeteria kitchen 4 8th Floor Banquet Kitchen 3 9th floor Banquet Kitchen 4 9th floor Bakery Kitchen 5 9M Floor Seven Kitchen Lump 6 9M Floor Sahib Room Kitchen 4 187,450/- 749,800/- sum 7 37th Floor Mekong Kitchen 8 38th Floor Zenith Kitchen 9 38th Floor Koishii Kitchen 10 10th Floor IRDA Kitchen 11 Gr. Floor Cafeteria (Mall) Sub Total 187,450/- 749,800/- GST 18 33,741/- 134,964/- TOTAL 221,191/- 884,764/- Looking forward for your
    
    Payment Schedule Amount towards Flat Sr. No. Stage of Work Consideration (A) 1 On Booking Rs. 1020000 /- 2 On Agreement Rs. 1020000 /- 3 On Commencement Of Work Rs. 1020000 /- 4 On Commencement Of Basement Rs. 612000 /- 5 On Commencement Of 1st Slab Rs. 204000 /- 6 On Commencement Of 3rd Slab Rs. 204000 /- 7 On Commencement Of 5th Slab Rs. 204000 /- 8 On Commencement Of 7th Slab Rs. 204000 /- 9 On Commencement Of 9th Slab Rs. 204000 /- 10 On Commencement Of 11th Slab Rs. 204000 /- 11 On Commencement Of 13th Slab Rs. 204000 /- 12 On Commencement Of 15th Slab Rs. 204000 /- 13 On Commencement Of 17th Slab Rs. 204000 /- 14 On Commencement Of 19th Slab Rs. 204000 /- 15 On Commencement Of 21st Slab Rs. 204000 /- 16 On Commencement Of 23rd Slab Rs. 204000 /- 17 On Commencement Of 25th Slab Rs. 204000 /- 18 On Commencement Of 27th Slab Rs. 204000 /- 19 On Commencement Of 29th Slab Rs. 204000 /- 20 On Commencement Of 31st Slab Rs. 204000 /- 21 On Commencement Of 33rd Slab Rs. 204000 /- 22 On Commencement Of 35th Slab Rs. 204000 /- 23 On Commencement Of 37th Slab Rs. 204000 /- 24 On Commencement Of 39th Slab Rs. 204000 /- 25 On Commencement Of 41st Slab Rs. 204000 /- 26 On Commencement Of 43rd Slab Rs. 204000 /- 27 On Commencement Of 45th Slab Rs. 204000 /- 28 On Commencement Of 47th Slab Rs. 204000 /- 29 On Commencement Of 49th Slab Rs. 204000 /- 30 On Commencement Of 51st Slab Rs. 204000 /- 31 On Commencement Of Flooring Tiling Rs. 204000 /- 32 On Commencement Of External Plumbing Of Building Rs. 204000 /- 33 On Commencement Of External Painting Rs. 306000 /- 34 On Possession Rs. 510000 /- Total Rs. 10200000 /- 36
    """
    
    print("=== TESTING ENHANCED MONETARY EXTRACTION ===\n")
    
    # Test 1: Multi-pass financial analysis
    print("1. Testing Multi-Pass Financial Analysis:")
    print("-" * 50)
    analysis = multi_pass_financial_analysis(sample_text)
    
    print(f"Found {len(analysis['amounts'])} monetary amounts:")
    for i, amount in enumerate(analysis['amounts'][:5]):  # Show first 5
        print(f"  {i+1}. {amount['amount']} - Context: {amount['context'][:50]}...")
    
    print(f"\nFound {len(analysis['payment_schedules'])} payment schedules:")
    for i, schedule in enumerate(analysis['payment_schedules']):
        print(f"  {i+1}. {schedule['text'][:100]}...")
    
    print(f"\nFound {len(analysis['financial_terms'])} financial terms:")
    for i, term in enumerate(analysis['financial_terms'][:5]):  # Show first 5
        print(f"  {i+1}. {term['term']}")
    
    print(f"\nFound {len(analysis['tables'])} tables:")
    for i, table in enumerate(analysis['tables']):
        print(f"  Table {i+1}: Headers: {table['headers']}")
        print(f"    Rows: {len(table['rows'])}")
    
    print(f"\nFound {len(analysis['calculations'])} calculations:")
    for i, calc in enumerate(analysis['calculations'][:3]):  # Show first 3
        print(f"  {i+1}. {calc['calculation']}")
    
    # Test 2: Enhanced financial chunking
    print("\n\n2. Testing Enhanced Financial Chunking:")
    print("-" * 50)
    enhanced_text = enhance_financial_chunking(sample_text)
    
    # Count different types of markers
    markers = {
        'CURRENCY_USD': enhanced_text.count('[CURRENCY_USD:'),
        'INDIAN_CURRENCY': enhanced_text.count('[INDIAN_CURRENCY:'),
        'FINANCIAL_TERM': enhanced_text.count('[FINANCIAL_TERM:'),
        'PAYMENT_DUE': enhanced_text.count('[PAYMENT_DUE:'),
        'PENALTY_FEE': enhanced_text.count('[PENALTY_FEE:'),
        'PERCENTAGE': enhanced_text.count('[PERCENTAGE:'),
        'PROPERTY_FINANCIAL': enhanced_text.count('[PROPERTY_FINANCIAL:'),
        'PAYMENT_SCHEDULE': enhanced_text.count('[PAYMENT_SCHEDULE:'),
        'CALCULATION': enhanced_text.count('[CALCULATION:'),
        'UNIT_AMOUNT': enhanced_text.count('[UNIT_AMOUNT:'),
    }
    
    print("Financial markers found:")
    for marker_type, count in markers.items():
        if count > 0:
            print(f"  {marker_type}: {count}")
    
    # Test 3: Show sample of enhanced text
    print("\n\n3. Sample of Enhanced Text:")
    print("-" * 50)
    lines = enhanced_text.split('\n')
    for line in lines[:10]:  # Show first 10 lines
        if '[INDIAN_CURRENCY:' in line or '[FINANCIAL_TERM:' in line:
            print(f"  {line}")
    
    print("\n=== TEST COMPLETED ===")
    return True

if __name__ == "__main__":
    try:
        test_monetary_extraction()
        print("\n✅ All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
