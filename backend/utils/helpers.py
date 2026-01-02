"""
Utility Functions
Common helper functions used across services
"""

from typing import Dict, List, Any
import hashlib
import json
from datetime import datetime


def calculate_checksum(data: str) -> str:
    """Calculate SHA256 checksum of data"""
    return hashlib.sha256(data.encode()).hexdigest()


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat() if dt else None


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime"""
    try:
        return datetime.fromisoformat(timestamp_str)
    except:
        return None


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if denominator is zero"""
    return numerator / denominator if denominator != 0 else default


def calculate_percentage(part: float, whole: float) -> float:
    """Calculate percentage"""
    return safe_divide(part, whole) * 100


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def deduplicate_list(items: List[Any]) -> List[Any]:
    """Remove duplicates from list while preserving order"""
    seen = set()
    result = []
    for item in items:
        # Handle dict items
        item_key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    return result


def group_by(items: List[Dict], key: str) -> Dict[Any, List[Dict]]:
    """Group list of dicts by a key"""
    groups = {}
    for item in items:
        group_key = item.get(key)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    return groups


def calculate_average(numbers: List[float]) -> float:
    """Calculate average of list of numbers"""
    return safe_divide(sum(numbers), len(numbers))


def calculate_median(numbers: List[float]) -> float:
    """Calculate median of list of numbers"""
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n == 0:
        return 0.0
    if n % 2 == 0:
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    return sorted_numbers[n//2]


def calculate_standard_deviation(numbers: List[float]) -> float:
    """Calculate standard deviation"""
    if not numbers:
        return 0.0
    mean = calculate_average(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    return variance ** 0.5


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def normalize_path(path: str) -> str:
    """Normalize file path (cross-platform)"""
    return path.replace('\\', '/').strip()


def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return filename.split('.')[-1].lower() if '.' in filename else ''


def is_code_file(filename: str) -> bool:
    """Check if file is a code file"""
    code_extensions = [
        'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'h',
        'cs', 'go', 'rb', 'php', 'swift', 'kt', 'rs', 'scala'
    ]
    return get_file_extension(filename) in code_extensions


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split list into batches"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
