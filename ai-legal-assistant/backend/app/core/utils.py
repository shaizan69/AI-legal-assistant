"""
Utility functions and helpers
"""

import os
import hashlib
import mimetypes
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
from datetime import datetime, timedelta
import json
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    
    extension = filename.split('.')[-1].lower()
    return extension in allowed_extensions


def get_file_mime_type(file_path: str) -> str:
    """Get MIME type of a file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return ""


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep legal document formatting
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\{\}\-\'\"\/]', '', text)
    
    # Normalize line breaks
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()


def extract_metadata_from_text(text: str) -> Dict[str, Any]:
    """Extract metadata from document text"""
    metadata = {
        "word_count": len(text.split()),
        "character_count": len(text),
        "line_count": len(text.split('\n')),
        "extraction_date": datetime.utcnow().isoformat()
    }
    
    # Try to extract document title
    lines = text.split('\n')
    if lines:
        # First non-empty line might be title
        for line in lines[:5]:
            if line.strip() and len(line.strip()) > 10:
                metadata["potential_title"] = line.strip()[:100]
                break
    
    # Look for common legal document patterns
    patterns = {
        "agreement": r"(?i)(agreement|contract|terms and conditions)",
        "date": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        "parties": r"(?i)(between|party|parties)",
        "termination": r"(?i)(termination|expiration|expires)",
        "liability": r"(?i)(liability|indemnification|damages)",
        "payment": r"(?i)(payment|fee|cost|price|amount)",
        "confidentiality": r"(?i)(confidential|proprietary|non-disclosure)"
    }
    
    found_patterns = {}
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            found_patterns[pattern_name] = len(matches)
    
    metadata["patterns_found"] = found_patterns
    
    return metadata


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 160) -> List[str]:
    """Split text into overlapping chunks for processing with improved legal document handling"""
    if not text:
        return []
    
    # Enhance text for better financial information capture
    enhanced_text = enhance_financial_chunking(text)
    
    # Check if this is a property document with payment schedules
    is_property_doc = is_property_document(enhanced_text)
    
    if is_property_doc:
        # Use specialized chunking for property documents
        return chunk_property_document(enhanced_text, chunk_size, overlap)
    
    # First, try to split by legal document sections
    sections = split_by_legal_sections(enhanced_text)
    if len(sections) > 1:
        chunks = []
        for section in sections:
            if len(section.split()) <= chunk_size:
                chunks.append(section.strip())
            else:
                # Split large sections by sentences
                chunks.extend(split_by_sentences(section, chunk_size, overlap))
        return chunks
    
    # Fallback to word-based chunking
    words = enhanced_text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    
    return chunks


def is_property_document(text: str) -> bool:
    """Check if document is property-related with payment schedules"""
    property_indicators = [
        'property', 'real estate', 'land', 'house', 'apartment', 'flat', 'villa',
        'lease', 'rental', 'tenancy', 'agreement', 'deed', 'sale deed', 'purchase',
        'payment schedule', 'installment', 'down payment', 'monthly payment',
        'quarterly payment', 'annual payment', 'advance payment', 'security deposit',
        'maintenance', 'maintenance charges', 'property tax', 'registration',
        'stamp duty', 'brokerage', 'commission', 'possession', 'handover',
        'possession date', 'completion', 'construction', 'builder', 'developer'
    ]
    
    text_lower = text.lower()
    property_count = sum(1 for indicator in property_indicators if indicator in text_lower)
    
    # Also check for payment schedule patterns
    payment_patterns = [
        r'payment\s+schedule', r'installment\s+plan', r'payment\s+plan',
        r'monthly\s+installment', r'quarterly\s+installment', r'annual\s+installment',
        r'down\s+payment', r'advance\s+payment', r'security\s+deposit'
    ]
    
    payment_count = sum(1 for pattern in payment_patterns if re.search(pattern, text_lower))
    
    return property_count >= 3 or payment_count >= 2


def chunk_property_document(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Specialized chunking for property documents with payment schedules"""
    chunks = []
    
    # First, try to extract payment schedules as separate chunks
    payment_schedules = extract_payment_schedules(text)
    if payment_schedules:
        for schedule in payment_schedules:
            chunks.append(schedule)
    
    # Extract property-specific sections
    property_sections = extract_property_sections(text)
    for section in property_sections:
        if len(section.split()) <= chunk_size:
            chunks.append(section.strip())
        else:
            # Split large sections by sentences
            chunks.extend(split_by_sentences(section, chunk_size, overlap))
    
    # If no specific sections found, use enhanced word-based chunking
    if not chunks:
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
    
    return chunks


def extract_payment_schedules(text: str) -> List[str]:
    """Extract payment schedules from property documents"""
    import re
    
    schedules = []
    
    # Look for payment schedule patterns
    schedule_patterns = [
        r'(?:payment\s+schedule|installment\s+plan|payment\s+plan)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:monthly|quarterly|annual)\s+installment[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:down\s+payment|advance\s+payment)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:possession|handover|completion)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)'
    ]
    
    for pattern in schedule_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if len(match.strip()) > 50:  # Only include substantial content
                schedules.append(f"PAYMENT SCHEDULE:\n{match.strip()}")
    
    return schedules


def extract_property_sections(text: str) -> List[str]:
    """Extract property-specific sections from documents"""
    import re
    
    sections = []
    
    # Property-specific section patterns
    property_patterns = [
        r'(?:property\s+details|property\s+information)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:payment\s+terms|payment\s+conditions)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:possession\s+terms|possession\s+conditions)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:maintenance\s+charges|maintenance\s+fees)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:registration\s+charges|stamp\s+duty)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:brokerage|commission)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:penalty|late\s+fee)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:refund\s+policy|cancellation)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)'
    ]
    
    for pattern in property_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if len(match.strip()) > 50:  # Only include substantial content
                sections.append(match.strip())
    
    return sections


def split_by_legal_sections(text: str) -> List[str]:
    """Split text by common legal document sections"""
    import re
    
    # Common legal section patterns
    section_patterns = [
        r'\n\s*(?:ARTICLE|Article)\s+[IVX\d]+[\.:]?\s*',  # Articles
        r'\n\s*(?:SECTION|Section)\s+[IVX\d]+[\.:]?\s*',  # Sections
        r'\n\s*(?:CLAUSE|Clause)\s+[IVX\d]+[\.:]?\s*',    # Clauses
        r'\n\s*(?:PARAGRAPH|Paragraph)\s+[IVX\d]+[\.:]?\s*', # Paragraphs
        r'\n\s*(?:SUBSECTION|Subsection)\s+[IVX\d]+[\.:]?\s*', # Subsections
        r'\n\s*(?:PART|Part)\s+[IVX\d]+[\.:]?\s*',         # Parts
        r'\n\s*(?:CHAPTER|Chapter)\s+[IVX\d]+[\.:]?\s*',   # Chapters
        r'\n\s*(?:SCHEDULE|Schedule)\s+[IVX\d]+[\.:]?\s*', # Schedules
        r'\n\s*(?:APPENDIX|Appendix)\s+[IVX\d]+[\.:]?\s*', # Appendices
    ]
    
    # Try each pattern
    for pattern in section_patterns:
        sections = re.split(pattern, text, flags=re.IGNORECASE)
        if len(sections) > 1:
            return [s.strip() for s in sections if s.strip()]
    
    return [text]  # Return original text if no sections found


def split_by_sentences(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text by sentences while respecting chunk size"""
    import re
    
    # Split by sentences (period, exclamation, question mark)
    sentences = re.split(r'[.!?]+\s+', text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_size = len(sentence_words)
        
        if current_size + sentence_size > chunk_size and current_chunk:
            # Create chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            overlap_words = current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
            current_chunk = overlap_words + sentence_words
            current_size = len(current_chunk)
        else:
            current_chunk.extend(sentence_words)
            current_size += sentence_size
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def format_legal_date(date_str: str) -> Optional[str]:
    """Format various date formats to ISO format"""
    if not date_str:
        return None
    
    # Common date patterns
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
        r'(\d{1,2})\s+(\w+)\s+(\d{4})',        # DD Month YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    # Try different interpretations
                    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            date_obj = datetime.strptime(f"{groups[0]}/{groups[1]}/{groups[2]}", fmt)
                            return date_obj.isoformat()
                        except ValueError:
                            continue
            except Exception:
                continue
    
    return None


def extract_legal_entities(text: str) -> Dict[str, List[str]]:
    """Extract legal entities from text"""
    entities = {
        "dates": [],
        "amounts": [],
        "parties": [],
        "clauses": []
    }
    
    # Extract dates
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+\s+\d{1,2},?\s+\d{4}\b'
    entities["dates"] = re.findall(date_pattern, text)
    
    # Extract monetary amounts
    amount_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|usd)\b'
    entities["amounts"] = re.findall(amount_pattern, text, re.IGNORECASE)
    
    # Extract party names (simple pattern)
    party_pattern = r'(?:between|party|parties)\s+([A-Z][a-zA-Z\s&,]+?)(?:\s+and|\s+\(|\s+whereas)'
    entities["parties"] = re.findall(party_pattern, text, re.IGNORECASE)
    
    # Extract clause references
    clause_pattern = r'(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)*)'
    entities["clauses"] = re.findall(clause_pattern, text, re.IGNORECASE)
    
    return entities


def create_document_fingerprint(text: str) -> str:
    """Create a unique fingerprint for a document"""
    # Normalize text for fingerprinting
    normalized = re.sub(r'\s+', ' ', text.lower())
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Create hash
    return hashlib.md5(normalized.encode()).hexdigest()


def safe_json_serialize(obj: Any) -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error serializing to JSON: {e}")
        return json.dumps({"error": "Serialization failed"})


def parse_legal_document_structure(text: str) -> Dict[str, Any]:
    """Parse the structure of a legal document"""
    structure = {
        "sections": [],
        "clauses": [],
        "definitions": [],
        "schedules": []
    }
    
    lines = text.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Look for section headers
        if re.match(r'^\d+\.?\s+[A-Z]', line) or re.match(r'^[A-Z][A-Z\s]+$', line):
            current_section = {
                "title": line,
                "line_number": i + 1,
                "content": []
            }
            structure["sections"].append(current_section)
        
        # Look for clause numbers
        elif re.match(r'^\d+\.\d+', line):
            clause = {
                "number": line.split()[0],
                "content": line,
                "line_number": i + 1
            }
            structure["clauses"].append(clause)
            if current_section:
                current_section["content"].append(clause)
        
        # Look for definitions
        elif 'means' in line.lower() or 'shall mean' in line.lower():
            definition = {
                "content": line,
                "line_number": i + 1
            }
            structure["definitions"].append(definition)
        
        # Look for schedules/appendices
        elif 'schedule' in line.lower() or 'appendix' in line.lower():
            schedule = {
                "title": line,
                "line_number": i + 1
            }
            structure["schedules"].append(schedule)
    
    return structure


def validate_document_content(text: str) -> Dict[str, Any]:
    """Validate document content for legal document characteristics"""
    validation = {
        "is_valid": True,
        "warnings": [],
        "errors": []
    }
    
    if not text or len(text.strip()) < 100:
        validation["is_valid"] = False
        validation["errors"].append("Document too short to be a valid legal document")
        return validation
    
    # Check for minimum word count
    word_count = len(text.split())
    if word_count < 50:
        validation["warnings"].append("Document has very few words")
    
    # Check for legal document indicators
    legal_indicators = [
        "agreement", "contract", "terms", "conditions", "party", "parties",
        "whereas", "hereby", "shall", "obligation", "liability", "indemnification"
    ]
    
    text_lower = text.lower()
    found_indicators = [indicator for indicator in legal_indicators if indicator in text_lower]
    
    if len(found_indicators) < 3:
        validation["warnings"].append("Document may not be a legal document")
    
    # Check for proper structure
    if not re.search(r'\d+\.', text):
        validation["warnings"].append("Document lacks numbered sections")
    
    return validation


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def extract_tables_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract table data from text using various patterns"""
    tables = []
    lines = text.split('\n')
    
    current_table = None
    table_start = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line looks like a table header (contains multiple columns separated by spaces/tabs)
        if is_table_header(line):
            if current_table:
                # Save previous table
                tables.append(current_table)
            
            # Start new table
            current_table = {
                "start_line": i,
                "headers": parse_table_row(line),
                "rows": [],
                "type": "financial" if contains_financial_data(line) else "general"
            }
            table_start = i
            
        # Check if line looks like a table row
        elif current_table and is_table_row(line):
            row_data = parse_table_row(line)
            if len(row_data) >= len(current_table["headers"]):
                current_table["rows"].append({
                    "line_number": i,
                    "data": row_data
                })
        
        # Check if we've reached the end of a table (empty line or non-table content)
        elif current_table and (not line or not is_table_row(line)):
            if current_table["rows"]:  # Only save if we have data
                current_table["end_line"] = i - 1
                tables.append(current_table)
            current_table = None
            table_start = None
    
    # Don't forget the last table
    if current_table and current_table["rows"]:
        current_table["end_line"] = len(lines) - 1
        tables.append(current_table)
    
    return tables


def is_table_header(line: str) -> bool:
    """Check if a line looks like a table header"""
    # Look for patterns like: "Item | Quantity | Price" or "Sr. No.  Description  Amount"
    if len(line) < 10:
        return False
    
    # Check for multiple columns separated by spaces/tabs/pipes
    columns = re.split(r'\s{2,}|\t+|\|', line)
    if len(columns) < 2:
        return False
    
    # Check if it contains table-like words
    table_indicators = [
        'item', 'description', 'quantity', 'qty', 'amount', 'price', 'cost', 'total',
        'sr', 'no', 's.no', 'sno', 'sl', 'serial', 'particulars', 'details',
        'unit', 'rate', 'value', 'sum', 'subtotal', 'tax', 'gst', 'vat',
        'payment', 'fee', 'charge', 'penalty', 'interest', 'discount'
    ]
    
    line_lower = line.lower()
    indicator_count = sum(1 for indicator in table_indicators if indicator in line_lower)
    
    return indicator_count >= 1 and len(columns) >= 2


def is_table_row(line: str) -> bool:
    """Check if a line looks like a table row"""
    if len(line) < 5:
        return False
    
    # Check for multiple columns separated by spaces/tabs
    columns = re.split(r'\s{2,}|\t+', line)
    if len(columns) < 2:
        return False
    
    # Check if it contains data patterns (numbers, amounts, etc.)
    data_patterns = [
        r'\d+',  # Numbers
        r'[\d,]+(?:\.\d{2})?',  # Amounts
        r'[\d,]+(?:\.\d{2})?/-',  # Indian currency
        r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
        r'[\d,]+(?:\.\d{2})?\s*%',  # Percentages
    ]
    
    has_data = any(re.search(pattern, line) for pattern in data_patterns)
    return has_data or len(columns) >= 3


def parse_table_row(line: str) -> List[str]:
    """Parse a table row into columns"""
    # Split by multiple spaces, tabs, or pipes
    columns = re.split(r'\s{2,}|\t+|\|', line)
    return [col.strip() for col in columns if col.strip()]


def contains_financial_data(line: str) -> bool:
    """Check if a line contains financial data"""
    financial_patterns = [
        r'[\d,]+(?:\.\d{2})?/-',  # Indian currency
        r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
        r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|INR|rupees?)',  # Currency codes
        r'[\d,]+(?:\.\d{2})?\s*%',  # Percentages
        r'(?:amount|price|cost|fee|charge|total|sum|value)',  # Financial terms
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in financial_patterns)


def format_table_for_chunking(table: Dict[str, Any]) -> str:
    """Format table data for better chunking and retrieval"""
    if not table or not table.get("rows"):
        return ""
    
    formatted_lines = []
    
    # Add table header
    headers = table["headers"]
    formatted_lines.append("TABLE DATA:")
    formatted_lines.append("| " + " | ".join(headers) + " |")
    formatted_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Add table rows
    for row in table["rows"]:
        row_data = row["data"]
        # Pad row data to match header length
        while len(row_data) < len(headers):
            row_data.append("")
        formatted_lines.append("| " + " | ".join(row_data) + " |")
    
    return "\n".join(formatted_lines)


def multi_pass_financial_analysis(text: str) -> Dict[str, Any]:
    """Multi-pass analysis to extract comprehensive financial data"""
    analysis = {
        "amounts": [],
        "currencies": [],
        "payment_schedules": [],
        "financial_terms": [],
        "tables": [],
        "calculations": [],
        "contexts": {}
    }
    
    # Pass 1: Extract all monetary amounts with context
    amount_patterns = [
        r'[\d,]+(?:\.\d{2})?/-',  # Indian currency
        r'\$[\d,]+(?:\.\d{2})?',  # USD
        r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|CAD|AUD|JPY|CHF|CNY|INR)',  # Currency codes
        r'[\d,]+(?:\.\d{2})?\s*rupees?',  # Written rupees
        r'[\d,]+(?:\.\d{2})?\s*rs\.?',  # Rs abbreviation
        r'[\d,]+(?:\.\d{2})?\s*₹',  # Rupee symbol
    ]
    
    for pattern in amount_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount = match.group(0)
            start, end = match.span()
            
            # Extract context around the amount (50 chars before and after)
            context_start = max(0, start - 50)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end]
            
            analysis["amounts"].append({
                "amount": amount,
                "position": start,
                "context": context,
                "pattern_type": "currency"
            })
    
    # Pass 2: Extract payment schedules
    schedule_patterns = [
        r'(?:payment\s+schedule|installment\s+plan|payment\s+plan)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:monthly|quarterly|annual)\s+installment[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
        r'(?:down\s+payment|advance\s+payment)[\s\S]*?(?=\n\s*\n|\n\s*[A-Z]|\Z)',
    ]
    
    for pattern in schedule_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            schedule_text = match.group(0)
            analysis["payment_schedules"].append({
                "text": schedule_text,
                "position": match.start(),
                "type": "payment_schedule"
            })
    
    # Pass 3: Extract financial terms with amounts
    financial_term_patterns = [
        r'(?:payment|fee|cost|charge|price|amount|total|sum|value|worth|budget|expense|revenue|income|salary|wage|bonus|penalty|fine|refund|deposit|advance|installment|interest|tax|commission|royalty|rent|lease|purchase|sale|compensation|benefits|allowance|stipend|pension|retirement|insurance|premium|deductible|coverage|claim|settlement|award|damages|restitution|reimbursement|subsidy|grant|funding|sponsorship|endorsement|licensing|franchise|dividend|share|stock|bond|security|asset|liability|equity|capital|fund|treasury|budget|forecast|projection|estimate|quotation|proposal|bid|tender|contract|agreement|deal|transaction|exchange|trade|commerce|business|enterprise|corporation|company|firm|partnership|sole proprietorship|llc|inc|corp|ltd|llp|pllc|pc|pa)\s*:?\s*[\d,]+(?:\.\d{2})?',
    ]
    
    for pattern in financial_term_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            term_text = match.group(0)
            analysis["financial_terms"].append({
                "term": term_text,
                "position": match.start(),
                "type": "financial_term"
            })
    
    # Pass 4: Extract tables
    tables = extract_tables_from_text(text)
    for table in tables:
        analysis["tables"].append({
            "headers": table["headers"],
            "rows": table["rows"],
            "type": table["type"],
            "start_line": table["start_line"],
            "end_line": table.get("end_line", table["start_line"])
        })
    
    # Pass 5: Extract calculations
    calculation_patterns = [
        r'(?:total|sum|subtotal|grand total|final amount|final cost|final price|final value|final worth|final budget|final expense|final revenue|final income|final salary|final wage|final bonus|final penalty|final fine|final refund|final deposit|final advance|final installment|final interest|final tax|final commission|final royalty|final rent|final lease|final purchase|final sale|final compensation|final benefits|final allowance|final stipend|final pension|final retirement|final insurance|final premium|final deductible|final coverage|final claim|final settlement|final award|final damages|final restitution|final reimbursement|final subsidy|final grant|final funding|final sponsorship|final endorsement|final licensing|final franchise|final dividend|final share|final stock|final bond|final security|final asset|final liability|final equity|final capital|final fund|final treasury|final budget|final forecast|final projection|final estimate|final quotation|final proposal|final bid|final tender|final contract|final agreement|final deal|final transaction|final exchange|final trade|final commerce|final business|final enterprise|final corporation|final company|final firm|final partnership|final sole proprietorship|final llc|final inc|final corp|final ltd|final llp|final pllc|final pc|final pa)\s+(?:is|equals?|=\s*)?\s*[\d,]+(?:\.\d{2})?',
    ]
    
    for pattern in calculation_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            calc_text = match.group(0)
            analysis["calculations"].append({
                "calculation": calc_text,
                "position": match.start(),
                "type": "calculation"
            })
    
    return analysis


def enhance_financial_chunking(text: str) -> str:
    """Enhanced financial chunking with advanced monetary data extraction"""
    # First, extract and format tables
    tables = extract_tables_from_text(text)
    
    # Advanced financial pattern recognition with comprehensive regex patterns
    financial_patterns = [
        # Enhanced currency patterns
        (r'\$[\d,]+(?:\.\d{2})?', r'[CURRENCY_USD: \g<0>]'),
        (r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|CAD|AUD|JPY|CHF|CNY|INR)', r'[CURRENCY: \g<0>]'),
        
        # Indian currency formats (enhanced)
        (r'[\d,]+(?:\.\d{2})?/-', r'[INDIAN_CURRENCY: \g<0>]'),
        (r'[\d,]+(?:\.\d{2})?\s*/-', r'[INDIAN_CURRENCY: \g<0>]'),
        (r'[\d,]+(?:\.\d{2})?\s*rupees?', r'[INDIAN_CURRENCY: \g<0>]'),
        (r'[\d,]+(?:\.\d{2})?\s*rs\.?', r'[INDIAN_CURRENCY: \g<0>]'),
        (r'[\d,]+(?:\.\d{2})?\s*₹', r'[INDIAN_CURRENCY: \g<0>]'),
        
        # Written amounts (enhanced)
        (r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|trillion|lakh|crore)\s+(?:dollars?|USD|EUR|GBP|rupees?|rs\.?)', r'[WRITTEN_AMOUNT: \g<0>]'),
        
        # Financial terms with amounts (enhanced)
        (r'(?:payment|fee|cost|charge|price|amount|total|sum|value|worth|budget|expense|revenue|income|salary|wage|bonus|penalty|fine|refund|deposit|advance|installment|interest|tax|commission|royalty|rent|lease|purchase|sale|compensation|benefits|allowance|stipend|pension|retirement|insurance|premium|deductible|coverage|claim|settlement|award|damages|restitution|reimbursement|subsidy|grant|funding|sponsorship|endorsement|licensing|franchise|dividend|share|stock|bond|security|asset|liability|equity|capital|fund|treasury|budget|forecast|projection|estimate|quotation|proposal|bid|tender|contract|agreement|deal|transaction|exchange|trade|commerce|business|enterprise|corporation|company|firm|partnership|sole proprietorship|llc|inc|corp|ltd|llp|pllc|pc|pa)\s*:?\s*[\d,]+(?:\.\d{2})?', r'[FINANCIAL_TERM: \g<0>]'),
        (r'(?:payment|fee|cost|charge|price|amount|total|sum|value|worth|budget|expense|revenue|income|salary|wage|bonus|penalty|fine|refund|deposit|advance|installment|interest|tax|commission|royalty|rent|lease|purchase|sale|compensation|benefits|allowance|stipend|pension|retirement|insurance|premium|deductible|coverage|claim|settlement|award|damages|restitution|reimbursement|subsidy|grant|funding|sponsorship|endorsement|licensing|franchise|dividend|share|stock|bond|security|asset|liability|equity|capital|fund|treasury|budget|forecast|projection|estimate|quotation|proposal|bid|tender|contract|agreement|deal|transaction|exchange|trade|commerce|business|enterprise|corporation|company|firm|partnership|sole proprietorship|llc|inc|corp|ltd|llp|pllc|pc|pa)\s+of\s*[\d,]+(?:\.\d{2})?', r'[FINANCIAL_TERM: \g<0>]'),
        
        # Payment terms (enhanced)
        (r'(?:due|payable|payable on|payment due|installment due|rent due|fee due|tax due|interest due|penalty due|fine due|refund due|deposit due|advance due|commission due|royalty due|rent due|lease due|purchase due|sale due|compensation due|benefits due|allowance due|stipend due|pension due|retirement due|insurance due|premium due|deductible due|coverage due|claim due|settlement due|award due|damages due|restitution due|reimbursement due|subsidy due|grant due|funding due|sponsorship due|endorsement due|licensing due|franchise due|dividend due|share due|stock due|bond due|security due|asset due|liability due|equity due|capital due|fund due|treasury due|budget due|forecast due|projection due|estimate due|quotation due|proposal due|bid due|tender due|contract due|agreement due|deal due|transaction due|exchange due|trade due|commerce due|business due|enterprise due|corporation due|company due|firm due|partnership due|sole proprietorship due|llc due|inc due|corp due|ltd due|llp due|pllc due|pc due|pa due)\s*:?\s*[\d,]+(?:\.\d{2})?', r'[PAYMENT_DUE: \g<0>]'),
        (r'(?:due|payable|payable on|payment due|installment due|rent due|fee due|tax due|interest due|penalty due|fine due|refund due|deposit due|advance due|commission due|royalty due|rent due|lease due|purchase due|sale due|compensation due|benefits due|allowance due|stipend due|pension due|retirement due|insurance due|premium due|deductible due|coverage due|claim due|settlement due|award due|damages due|restitution due|reimbursement due|subsidy due|grant due|funding due|sponsorship due|endorsement due|licensing due|franchise due|dividend due|share due|stock due|bond due|security due|asset due|liability due|equity due|capital due|fund due|treasury due|budget due|forecast due|projection due|estimate due|quotation due|proposal due|bid due|tender due|contract due|agreement due|deal due|transaction due|exchange due|trade due|commerce due|business due|enterprise due|corporation due|company due|firm due|partnership due|sole proprietorship due|llc due|inc due|corp due|ltd due|llp due|pllc due|pc due|pa due)\s+on\s*[\d,]+(?:\.\d{2})?', r'[PAYMENT_DUE: \g<0>]'),
        
        # Penalties and fees (enhanced)
        (r'(?:late fee|penalty|interest|fine|overdue|default|breach|violation|non-compliance|non-payment|delayed payment|missed payment|skipped payment|partial payment|incomplete payment|insufficient payment|excessive payment|unauthorized payment|fraudulent payment|disputed payment|chargeback|reversal|refund|cancellation|termination|early termination|premature termination|breach of contract|material breach|minor breach|substantial breach|fundamental breach|anticipatory breach|actual breach|constructive breach|repudiatory breach|renunciatory breach|discharge|performance|non-performance|partial performance|defective performance|delayed performance|late performance|early performance|premature performance|excessive performance|insufficient performance|incomplete performance|defective performance|non-conforming performance|conforming performance|satisfactory performance|unsatisfactory performance|defective performance|non-conforming performance|conforming performance|satisfactory performance|unsatisfactory performance)\s*:?\s*[\d,]+(?:\.\d{2})?', r'[PENALTY_FEE: \g<0>]'),
        (r'(?:late fee|penalty|interest|fine|overdue|default|breach|violation|non-compliance|non-payment|delayed payment|missed payment|skipped payment|partial payment|incomplete payment|insufficient payment|excessive payment|unauthorized payment|fraudulent payment|disputed payment|chargeback|reversal|refund|cancellation|termination|early termination|premature termination|breach of contract|material breach|minor breach|substantial breach|fundamental breach|anticipatory breach|actual breach|constructive breach|repudiatory breach|renunciatory breach|discharge|performance|non-performance|partial performance|defective performance|delayed performance|late performance|early performance|premature performance|excessive performance|insufficient performance|incomplete performance|defective performance|non-conforming performance|conforming performance|satisfactory performance|unsatisfactory performance|defective performance|non-conforming performance|conforming performance|satisfactory performance|unsatisfactory performance)\s+of\s*[\d,]+(?:\.\d{2})?', r'[PENALTY_FEE: \g<0>]'),
        
        # Percentage-based amounts (enhanced)
        (r'[\d,]+(?:\.\d{2})?\s*%', r'[PERCENTAGE: \g<0>]'),
        (r'(?:interest|rate|commission|fee|discount|markup|margin|profit|loss|tax|vat|gst|service tax|excise|duty|customs|import|export|tariff|quota|subsidy|incentive|rebate|refund|cashback|bonus|penalty|fine|late fee|overdue|default|breach|violation|non-compliance|non-payment|delayed payment|missed payment|skipped payment|partial payment|incomplete payment|insufficient payment|excessive payment|unauthorized payment|fraudulent payment|disputed payment|chargeback|reversal|refund|cancellation|termination|early termination|premature termination|breach of contract|material breach|minor breach|substantial breach|fundamental breach|anticipatory breach|actual breach|constructive breach|repudiatory breach|renunciatory breach|discharge|performance|non-performance|partial performance|defective performance|delayed performance|late performance|early performance|premature performance|excessive performance|insufficient performance|incomplete performance|defective performance|non-conforming performance|conforming performance|satisfactory performance|unsatisfactory performance|defective performance|non-conforming performance|conforming performance|satisfactory performance|unsatisfactory performance)\s+of\s*[\d,]+(?:\.\d{2})?\s*%', r'[PERCENTAGE_TERM: \g<0>]'),
        
        # Property-specific financial terms (enhanced)
        (r'(?:down payment|advance payment|security deposit|maintenance|maintenance charges|property tax|registration|stamp duty|brokerage|commission|possession|handover|completion|construction|builder|developer|architect|contractor|subcontractor|supplier|vendor|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional)\s*:?\s*[\d,]+(?:\.\d{2})?', r'[PROPERTY_FINANCIAL: \g<0>]'),
        (r'(?:down payment|advance payment|security deposit|maintenance|maintenance charges|property tax|registration|stamp duty|brokerage|commission|possession|handover|completion|construction|builder|developer|architect|contractor|subcontractor|supplier|vendor|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional)\s+of\s*[\d,]+(?:\.\d{2})?', r'[PROPERTY_FINANCIAL: \g<0>]'),
        
        # Payment schedule terms (enhanced)
        (r'(?:monthly|quarterly|annual|installment|payment schedule|payment plan|milestone|stage|phase|period|term|duration|tenure|lease|rental|subscription|membership|license|permit|authorization|approval|clearance|certification|accreditation|qualification|registration|enrollment|admission|acceptance|confirmation|acknowledgment|receipt|delivery|shipment|transport|logistics|warehousing|storage|inventory|stock|supply|procurement|purchasing|sourcing|vendor|supplier|contractor|subcontractor|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional)\s*:?\s*[\d,]+(?:\.\d{2})?', r'[PAYMENT_SCHEDULE: \g<0>]'),
        (r'(?:monthly|quarterly|annual|installment|payment schedule|payment plan|milestone|stage|phase|period|term|duration|tenure|lease|rental|subscription|membership|license|permit|authorization|approval|clearance|certification|accreditation|qualification|registration|enrollment|admission|acceptance|confirmation|acknowledgment|receipt|delivery|shipment|transport|logistics|warehousing|storage|inventory|stock|supply|procurement|purchasing|sourcing|vendor|supplier|contractor|subcontractor|consultant|advisor|agent|broker|intermediary|middleman|facilitator|coordinator|manager|supervisor|foreman|engineer|technician|specialist|expert|professional)\s+of\s*[\d,]+(?:\.\d{2})?', r'[PAYMENT_SCHEDULE: \g<0>]'),
        
        # Financial calculations (enhanced)
        (r'(?:total|sum|subtotal|grand total|final amount|final cost|final price|final value|final worth|final budget|final expense|final revenue|final income|final salary|final wage|final bonus|final penalty|final fine|final refund|final deposit|final advance|final installment|final interest|final tax|final commission|final royalty|final rent|final lease|final purchase|final sale|final compensation|final benefits|final allowance|final stipend|final pension|final retirement|final insurance|final premium|final deductible|final coverage|final claim|final settlement|final award|final damages|final restitution|final reimbursement|final subsidy|final grant|final funding|final sponsorship|final endorsement|final licensing|final franchise|final dividend|final share|final stock|final bond|final security|final asset|final liability|final equity|final capital|final fund|final treasury|final budget|final forecast|final projection|final estimate|final quotation|final proposal|final bid|final tender|final contract|final agreement|final deal|final transaction|final exchange|final trade|final commerce|final business|final enterprise|final corporation|final company|final firm|final partnership|final sole proprietorship|final llc|final inc|final corp|final ltd|final llp|final pllc|final pc|final pa)\s+(?:is|equals?|=\s*)?\s*[\d,]+(?:\.\d{2})?', r'[CALCULATION: \g<0>]'),
        
        # Enhanced amount patterns for better detection
        (r'[\d,]+(?:\.\d{2})?\s*(?:per|each|per unit|per item|per hour|per day|per week|per month|per year|per annum|per sq\.?ft|per sq\.?m|per acre|per hectare|per kg|per lb|per ton|per tonne|per liter|per gallon|per piece|per unit|per service|per visit|per call|per transaction|per order|per shipment|per delivery|per installation|per setup|per configuration|per customization|per integration|per migration|per upgrade|per maintenance|per support|per training|per consultation|per advice|per recommendation|per suggestion|per proposal|per plan|per strategy|per solution|per implementation|per execution|per completion|per delivery|per handover|per transfer|per assignment|per project|per task|per job|per work|per service|per product|per item|per unit|per piece|per lot|per batch|per shipment|per delivery|per installation|per setup|per configuration|per customization|per integration|per migration|per upgrade|per maintenance|per support|per training|per consultation|per advice|per recommendation|per suggestion|per proposal|per plan|per strategy|per solution|per implementation|per execution|per completion|per delivery|per handover|per transfer|per assignment|per project|per task|per job|per work|per service|per product|per item|per unit|per piece|per lot|per batch)', r'[UNIT_AMOUNT: \g<0>]'),
    ]
    
    enhanced_text = text
    for pattern, replacement in financial_patterns:
        enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
    
    # Add formatted tables to the enhanced text
    if tables:
        table_section = "\n\n" + "="*50 + "\nEXTRACTED TABLES:\n" + "="*50 + "\n"
        for i, table in enumerate(tables):
            table_section += f"\nTABLE {i+1}:\n"
            table_section += format_table_for_chunking(table) + "\n"
        
        enhanced_text += table_section
    
    return enhanced_text
