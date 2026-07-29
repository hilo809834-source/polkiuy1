"""
Secrets Manager - nothing hardcoded, nothing logged in plaintext.

Per ARCHITECTURE.md subsystem B:
- Secrets manager: nothing hardcoded, nothing logged in plaintext.
- Lifecycle hooks: explicit, deterministic checks fired at defined points 
  (after any dependency change, before any outbound log line, before any commit), 
  not enforcement buried inside a large function where it's easy to silently skip.

Phase 1 DoD: a deliberately planted fake secret in a source file gets caught 
by a real check before it would reach a commit or a log line.
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from core.config.settings import SECRETS_PATTERNS, LOG_REDACTION_PATTERNS


class SecretsManager:
    """
    Detects and prevents secrets from leaking into commits or logs.
    Uses regex patterns to scan files before commit and log output before emission.
    """
    
    def __init__(self):
        self._patterns = [re.compile(p) for p in SECRETS_PATTERNS]
        self._log_redaction_patterns = [
            (re.compile(orig, re.IGNORECASE), repl) 
            for orig, repl in LOG_REDACTION_PATTERNS
        ]
    
    def scan_file(self, file_path: str) -> List[Tuple[str, int, str]]:
        """
        Scan a single file for secrets.
        Returns list of (matched_pattern, line_number, line_content).
        """
        findings = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern in self._patterns:
                        match = pattern.search(line)
                        if match:
                            findings.append((
                                pattern.pattern,
                                line_num,
                                line.rstrip()
                            ))
        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)
        return findings
    
    def scan_directory(self, directory: str, extensions: Optional[List[str]] = None) -> dict:
        """
        Recursively scan a directory for secrets.
        extensions: list of file extensions to scan (e.g., ['.py', '.js']).
                   None means scan all files.
        Returns dict mapping file_path to list of findings.
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', 
                         '.rb', '.env', '.json', '.yaml', '.yml', '.toml', '.sh']
        
        findings = {}
        path = Path(directory)
        
        for ext in extensions:
            for file_path in path.rglob(f'*{ext}'):
                # Skip hidden directories and common build/test directories
                if any(part.startswith('.') or part in {'node_modules', 'build', 
                         'dist', '__pycache__', 'venv', '.venv', 'target'} 
                       for part in file_path.parts):
                    continue
                
                file_findings = self.scan_file(str(file_path))
                if file_findings:
                    findings[str(file_path)] = file_findings
        
        return findings
    
    def check_pre_commit(self, directory: str = ".") -> bool:
        """
        Run pre-commit check. Returns True if secrets are detected (should block commit).
        This is a lifecycle hook called before git commit.
        """
        findings = self.scan_directory(directory)
        if findings:
            print("\n🚨 SECRETS DETECTED - COMMIT BLOCKED", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            for file_path, file_findings in findings.items():
                print(f"\n📁 {file_path}", file=sys.stderr)
                for pattern, line_num, line in file_findings:
                    print(f"   Line {line_num}: {line[:80]}...", file=sys.stderr)
            print("\n" + "=" * 60, file=sys.stderr)
            print("Remove or redact secrets before committing.\n", file=sys.stderr)
            return True
        return False
    
    def redact_log(self, message: str) -> str:
        """
        Redact secrets from log output before emission.
        This is a lifecycle hook called before any outbound log line.
        """
        redacted = message
        for pattern, replacement in self._log_redaction_patterns:
            redacted = pattern.sub(replacement, redacted)
        return redacted


# Singleton instance
_secrets_manager: Optional[SecretsManager] = None

def get_secrets_manager() -> SecretsManager:
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def check_file_for_secrets(file_path: str) -> List[Tuple[str, int, str]]:
    """Convenience function to scan a single file."""
    return get_secrets_manager().scan_file(file_path)


def check_directory_for_secrets(directory: str) -> dict:
    """Convenience function to scan a directory."""
    return get_secrets_manager().scan_directory(directory)


def redact_log_message(message: str) -> str:
    """Convenience function to redact a log message."""
    return get_secrets_manager().redact_log(message)
