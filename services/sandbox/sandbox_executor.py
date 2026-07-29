"""
Sandbox Executor - containerized, isolated per task, resource-limited.

Per ARCHITECTURE.md subsystem B:
- Execution sandbox and workspace manager — isolated, containerized execution per task.

Phase 1 DoD: a deliberately runaway script actually gets killed by the timeout/memory limit.
A normal script running successfully is not sufficient evidence — the limit itself has to be shown working.
"""
import asyncio
import uuid
import sys
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import docker
from docker.errors import DockerException, NotFound

from core.config.settings import DOCKER_TIMEOUT_SECONDS, DOCKER_MEMORY_LIMIT, DOCKER_CPU_LIMIT


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    killed: bool = False
    killed_reason: Optional[str] = None


class SandboxExecutionError(Exception):
    """Raised when sandbox execution fails."""
    pass


class SandboxExecutor:
    """
    Executes code in isolated Docker containers with resource limits.
    """
    
    def __init__(self):
        self.timeout_seconds = DOCKER_TIMEOUT_SECONDS
        self.memory_limit = DOCKER_MEMORY_LIMIT
        self.cpu_limit = DOCKER_CPU_LIMIT
        self._client: Optional[docker.DockerClient] = None
    
    def _get_client(self) -> docker.DockerClient:
        """Get or create Docker client."""
        if self._client is None:
            try:
                self._client = docker.from_env()
                # Verify connection works
                self._client.ping()
            except DockerException as e:
                raise SandboxExecutionError(f"Cannot connect to Docker: {e}")
        return self._client
    
    def is_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            client = self._get_client()
            client.ping()
            return True
        except Exception:
            return False
    
    async def execute(
        self, 
        code: str, 
        language: str = "python",
        timeout_seconds: Optional[int] = None,
        memory_limit: Optional[str] = None
    ) -> SandboxResult:
        """
        Execute code in an isolated container.
        
        Args:
            code: The code to execute
            language: Programming language (python, node, etc.)
            timeout_seconds: Override default timeout
            memory_limit: Override default memory limit
            
        Returns:
            SandboxResult with execution output and metadata
        """
        timeout = timeout_seconds or self.timeout_seconds
        mem_limit = memory_limit or self.memory_limit
        
        client = self._get_client()
        container_id = str(uuid.uuid4())[:8]
        
        # Select image based on language
        image_map = {
            "python": "python:3.11-slim",
            "node": "node:20-slim",
            "bash": "bash:5.2",
        }
        image = image_map.get(language, "python:3.11-slim")
        
        # Prepare command
        if language == "python":
            command = f"python3 -c \"{code.replace('\"', '\\\"')}\""
        elif language == "node":
            command = f"node -e \"{code.replace('\"', '\\\"')}\""
        elif language == "bash":
            command = f"bash -c \"{code}\""
        else:
            command = f"python3 -c \"{code}\""
        
        host_config = None
        try:
            host_config = client.api.create_host_config(
                mem_limit=mem_limit,
                cpu_period=100000,
                cpu_quota=int(100000 * self.cpu_limit),
                auto_remove=True
            )
        except Exception as e:
            print(f"Warning: Could not create host config with limits: {e}", file=sys.stderr)
            host_config = client.api.create_host_config(auto_remove=True)
        
        try:
            container = client.containers.run(
                image,
                command,
                detach=True,
                mem_limit=mem_limit,
                cpu_period=100000,
                cpu_quota=int(100000 * self.cpu_limit),
                name=f"sandbox-{container_id}",
                stdout=True,
                stderr=True
            )
        except DockerException as e:
            raise SandboxExecutionError(f"Failed to start container: {e}")
        
        start_time = time.time()
        killed = False
        killed_reason = None
        
        try:
            # Wait for container with timeout
            result = container.wait(timeout=timeout)
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='ignore')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='ignore')
            exit_code = result.get('StatusCode', 0)
            
        except Exception as e:
            # Container likely timed out
            killed = True
            killed_reason = f"timeout_after_{timeout}s"
            stdout = ""
            stderr = str(e)
            exit_code = -1
            
            # Force kill the container
            try:
                container.kill()
            except Exception:
                pass
        
        finally:
            # Always clean up the container
            try:
                container.remove(force=True)
            except Exception:
                pass
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Check if we hit the timeout
        if not killed and duration_ms >= timeout * 1000 * 0.95:  # Within 5% of timeout
            # Container ran to completion but took most of the timeout
            pass
        
        return SandboxResult(
            success=exit_code == 0 and not killed,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            killed=killed,
            killed_reason=killed_reason
        )
    
    async def execute_with_timeout_test(
        self, 
        code: str, 
        timeout_seconds: int = 5,
        memory_limit: Optional[str] = None
    ) -> SandboxResult:
        """
        Execute code with a specific timeout for testing limit enforcement.
        This is specifically for Phase 1 DoD: demonstrating the timeout actually kills runaway code.
        """
        return await self.execute(
            code=code,
            language="python",
            timeout_seconds=timeout_seconds,
            memory_limit=memory_limit
        )


async def run_in_sandbox(
    code: str, 
    language: str = "python",
    timeout_seconds: Optional[int] = None
) -> SandboxResult:
    """
    Convenience function to run code in sandbox.
    """
    executor = SandboxExecutor()
    return await executor.execute(code, language, timeout_seconds)


# Singleton instance
_sandbox_executor: Optional[SandboxExecutor] = None

def get_sandbox_executor() -> SandboxExecutor:
    global _sandbox_executor
    if _sandbox_executor is None:
        _sandbox_executor = SandboxExecutor()
    return _sandbox_executor
