"""
Health check route
GET /health
"""
from pynext import JSONResponse
from datetime import datetime
import psutil
import platform
import sys

async def get():
    """Health check endpoint."""
    try:
        # System information
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "processor": platform.processor(),
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        # CPU information
        cpu_info = {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=1),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # Application health status
        app_status = "healthy"
        status_code = 200
        
        # Check if system resources are within acceptable limits
        warnings = []
        if memory.percent > 90:
            warnings.append("High memory usage")
        if cpu_info["percent"] > 90:
            warnings.append("High CPU usage")
        if disk_info["percent"] > 90:
            warnings.append("Low disk space")
        
        if warnings:
            app_status = "degraded"
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": app_status,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": "Available via system metrics",
                "version": "1.0.0",
                "framework": "PyNext",
                "system": system_info,
                "resources": {
                    "memory": memory_info,
                    "cpu": cpu_info,
                    "disk": disk_info
                },
                "warnings": warnings,
                "services": {
                    "database": "not_configured",
                    "cache": "not_configured",
                    "external_apis": "not_configured"
                },
                "checks": {
                    "memory_usage": "ok" if memory.percent < 80 else "warning" if memory.percent < 90 else "critical",
                    "cpu_usage": "ok" if cpu_info["percent"] < 80 else "warning" if cpu_info["percent"] < 90 else "critical",
                    "disk_space": "ok" if disk_info["percent"] < 80 else "warning" if disk_info["percent"] < 90 else "critical"
                },
                "message": "Service is running normally" if app_status == "healthy" else f"Service is {app_status} - {', '.join(warnings)}"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "message": "Health check failed"
            }
        )