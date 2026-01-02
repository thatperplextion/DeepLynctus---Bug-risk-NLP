"""
Security Scanning Service
Detects secrets, vulnerabilities, and security issues
"""

from typing import List, Dict
import re


class SecurityScanner:
    """Scans code for security vulnerabilities and exposed secrets"""
    
    def __init__(self, db):
        self.db = db
        
        # Patterns for detecting secrets
        self.secret_patterns = {
            "aws_access_key": r'AKIA[0-9A-Z]{16}',
            "aws_secret_key": r'aws_secret[_-]?key[\s]*=[\s]*[\'"][0-9a-zA-Z/+]{40}[\'"]',
            "api_key": r'api[_-]?key[\s]*[=:][\s]*[\'"][0-9a-zA-Z]{20,}[\'"]',
            "password": r'password[\s]*[=:][\s]*[\'"][^\'\"]{8,}[\'"]',
            "private_key": r'-----BEGIN (RSA |DSA )?PRIVATE KEY-----',
            "jwt_token": r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            "github_token": r'ghp_[0-9a-zA-Z]{36}',
            "stripe_key": r'sk_live_[0-9a-zA-Z]{24}',
            "database_url": r'(postgres|mysql|mongodb):\/\/[^\s]+',
            "generic_secret": r'(secret|token|key)[\s]*[=:][\s]*[\'"][^\'\"]{16,}[\'"]'
        }
        
        # OWASP Top 10 patterns
        self.owasp_patterns = {
            "sql_injection": r'(execute|query|SELECT|INSERT|UPDATE|DELETE).*(\+|concat).*[\'"]',
            "xss_vulnerability": r'innerHTML|document\.write|eval\(',
            "hardcoded_credentials": r'(username|password|api_key)[\s]*=[\s]*[\'"][^\'"]+[\'"]',
            "insecure_random": r'Math\.random\(',
            "weak_crypto": r'(MD5|SHA1)\(',
            "command_injection": r'(exec|eval|system|shell_exec)\(',
            "path_traversal": r'\.\.[/\\]',
            "xxe_vulnerability": r'XMLParser|parseXML'
        }
    
    async def scan_for_secrets(self, project_id: str) -> Dict:
        """Scan all files for exposed secrets"""
        files = await self.db.get_files_by_project(project_id)
        
        secrets_found = []
        
        for file in files:
            file_path = file.get('path', '')
            
            # Skip common non-code files
            if any(ext in file_path for ext in ['.jpg', '.png', '.pdf', '.zip']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for secret_type, pattern in self.secret_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        secrets_found.append({
                            "file": file_path,
                            "type": secret_type,
                            "line": line_num,
                            "severity": "critical",
                            "message": f"Potential {secret_type.replace('_', ' ')} exposed",
                            "matched_text": match.group()[:20] + "..." if len(match.group()) > 20 else match.group()
                        })
            except:
                continue
        
        return {
            "secrets_found": len(secrets_found),
            "files_affected": len(set(s['file'] for s in secrets_found)),
            "secrets": secrets_found
        }
    
    async def scan_for_vulnerabilities(self, project_id: str) -> Dict:
        """Scan for OWASP Top 10 vulnerabilities"""
        files = await self.db.get_files_by_project(project_id)
        
        vulnerabilities = []
        
        for file in files:
            file_path = file.get('path', '')
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for vuln_type, pattern in self.owasp_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        vulnerabilities.append({
                            "file": file_path,
                            "type": vuln_type,
                            "line": line_num,
                            "severity": self._get_vulnerability_severity(vuln_type),
                            "message": self._get_vulnerability_message(vuln_type),
                            "owasp_category": self._map_to_owasp_category(vuln_type)
                        })
            except:
                continue
        
        return {
            "vulnerabilities_found": len(vulnerabilities),
            "files_affected": len(set(v['file'] for v in vulnerabilities)),
            "vulnerabilities": vulnerabilities
        }
    
    async def calculate_security_score(self, project_id: str) -> Dict:
        """Calculate overall security score for the project"""
        secrets = await self.scan_for_secrets(project_id)
        vulns = await self.scan_for_vulnerabilities(project_id)
        
        # Start with perfect score
        score = 100
        
        # Deduct points for issues
        score -= secrets['secrets_found'] * 10  # -10 per secret
        score -= vulns['vulnerabilities_found'] * 5  # -5 per vulnerability
        
        score = max(0, score)  # Minimum 0
        
        return {
            "security_score": score,
            "grade": self._get_security_grade(score),
            "secrets_found": secrets['secrets_found'],
            "vulnerabilities_found": vulns['vulnerabilities_found'],
            "recommendation": self._get_security_recommendation(score)
        }
    
    def _get_vulnerability_severity(self, vuln_type: str) -> str:
        """Determine severity of vulnerability type"""
        critical = ["sql_injection", "command_injection"]
        high = ["xss_vulnerability", "path_traversal", "xxe_vulnerability"]
        
        if vuln_type in critical:
            return "critical"
        elif vuln_type in high:
            return "high"
        else:
            return "medium"
    
    def _get_vulnerability_message(self, vuln_type: str) -> str:
        """Get human-readable message for vulnerability"""
        messages = {
            "sql_injection": "Potential SQL injection vulnerability detected",
            "xss_vulnerability": "Cross-site scripting (XSS) vulnerability",
            "hardcoded_credentials": "Hardcoded credentials detected",
            "insecure_random": "Insecure random number generation",
            "weak_crypto": "Weak cryptographic algorithm used",
            "command_injection": "Command injection vulnerability",
            "path_traversal": "Path traversal vulnerability",
            "xxe_vulnerability": "XML External Entity (XXE) vulnerability"
        }
        return messages.get(vuln_type, f"Security issue: {vuln_type}")
    
    def _map_to_owasp_category(self, vuln_type: str) -> str:
        """Map vulnerability to OWASP Top 10 category"""
        mapping = {
            "sql_injection": "A03:2021 - Injection",
            "xss_vulnerability": "A03:2021 - Injection",
            "hardcoded_credentials": "A07:2021 - Identification and Authentication Failures",
            "insecure_random": "A02:2021 - Cryptographic Failures",
            "weak_crypto": "A02:2021 - Cryptographic Failures",
            "command_injection": "A03:2021 - Injection",
            "path_traversal": "A01:2021 - Broken Access Control",
            "xxe_vulnerability": "A05:2021 - Security Misconfiguration"
        }
        return mapping.get(vuln_type, "Other")
    
    def _get_security_grade(self, score: int) -> str:
        """Convert security score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _get_security_recommendation(self, score: int) -> str:
        """Get security recommendation based on score"""
        if score >= 90:
            return "Excellent security posture. Maintain current practices."
        elif score >= 70:
            return "Good security. Address remaining issues to improve further."
        elif score >= 50:
            return "Security needs improvement. Prioritize fixing critical issues."
        else:
            return "Critical security concerns. Immediate action required."
