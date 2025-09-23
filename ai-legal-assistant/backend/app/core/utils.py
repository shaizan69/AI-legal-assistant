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
    """Split text into overlapping chunks for processing"""
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    
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
