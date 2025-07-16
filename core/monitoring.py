"""
性能监控和指标收集模块
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    response_time_ms: float = 0.0
    request_count: int = 0
    error_count: int = 0

@dataclass
class APIMetrics:
    """API指标数据类"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    user_id: Optional[str] = None
    error_message: Optional[str] = None

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.api_metrics: deque = deque(maxlen=max_history)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # 统计数据
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        
    def start_monitoring(self, interval: float = 60.0):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("监控已经在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"性能监控已启动，采样间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("性能监控已停止")
    
    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.is_monitoring:
            try:
                metrics = self._collect_system_metrics()
                with self.lock:
                    self.metrics_history.append(metrics)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"监控数据收集失败: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> PerformanceMetrics:
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / 1024 / 1024
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # 网络使用情况
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv
        
        # 网络连接数
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = 0
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            active_connections=connections
        )
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, 
                       response_time_ms: float, user_id: Optional[str] = None,
                       error_message: Optional[str] = None):
        """记录API调用"""
        api_metric = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.now(),
            user_id=user_id,
            error_message=error_message
        )
        
        with self.lock:
            self.api_metrics.append(api_metric)
            
            # 更新统计数据
            key = f"{method} {endpoint}"
            self.request_counts[key] += 1
            
            if status_code >= 400:
                self.error_counts[key] += 1
            
            # 保持响应时间历史（最近100次）
            if len(self.response_times[key]) >= 100:
                self.response_times[key].pop(0)
            self.response_times[key].append(response_time_ms)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前指标"""
        with self.lock:
            if self.metrics_history:
                return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """获取指定时间范围内的指标历史"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                metric for metric in self.metrics_history
                if metric.timestamp >= cutoff_time
            ]
    
    def get_api_metrics(self, minutes: int = 60) -> List[APIMetrics]:
        """获取API指标"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                metric for metric in self.api_metrics
                if metric.timestamp >= cutoff_time
            ]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取汇总统计"""
        with self.lock:
            current_metrics = self.get_current_metrics()
            recent_api_metrics = self.get_api_metrics(60)  # 最近1小时
            
            # 计算API统计
            total_requests = len(recent_api_metrics)
            error_requests = len([m for m in recent_api_metrics if m.status_code >= 400])
            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
            
            # 计算平均响应时间
            if recent_api_metrics:
                avg_response_time = sum(m.response_time_ms for m in recent_api_metrics) / len(recent_api_metrics)
            else:
                avg_response_time = 0
            
            # 按端点统计
            endpoint_stats = defaultdict(lambda: {"count": 0, "errors": 0, "avg_time": 0})
            for metric in recent_api_metrics:
                key = f"{metric.method} {metric.endpoint}"
                endpoint_stats[key]["count"] += 1
                if metric.status_code >= 400:
                    endpoint_stats[key]["errors"] += 1
            
            # 计算平均响应时间
            for key, times in self.response_times.items():
                if times and key in endpoint_stats:
                    endpoint_stats[key]["avg_time"] = sum(times) / len(times)
            
            return {
                "system": {
                    "cpu_percent": current_metrics.cpu_percent if current_metrics else 0,
                    "memory_percent": current_metrics.memory_percent if current_metrics else 0,
                    "memory_used_mb": current_metrics.memory_used_mb if current_metrics else 0,
                    "disk_usage_percent": current_metrics.disk_usage_percent if current_metrics else 0,
                    "active_connections": current_metrics.active_connections if current_metrics else 0,
                },
                "api": {
                    "total_requests_1h": total_requests,
                    "error_requests_1h": error_requests,
                    "error_rate_percent": round(error_rate, 2),
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "endpoints": dict(endpoint_stats)
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def export_metrics(self, filepath: str):
        """导出指标到文件"""
        try:
            stats = self.get_summary_stats()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"指标已导出到 {filepath}")
        except Exception as e:
            logger.error(f"指标导出失败: {e}")
    
    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return {"status": "unknown", "message": "无监控数据"}
        
        issues = []
        
        # 检查CPU使用率
        if current_metrics.cpu_percent > 80:
            issues.append(f"CPU使用率过高: {current_metrics.cpu_percent}%")
        
        # 检查内存使用率
        if current_metrics.memory_percent > 85:
            issues.append(f"内存使用率过高: {current_metrics.memory_percent}%")
        
        # 检查磁盘使用率
        if current_metrics.disk_usage_percent > 90:
            issues.append(f"磁盘使用率过高: {current_metrics.disk_usage_percent}%")
        
        # 检查错误率
        recent_api_metrics = self.get_api_metrics(10)  # 最近10分钟
        if recent_api_metrics:
            error_count = len([m for m in recent_api_metrics if m.status_code >= 400])
            error_rate = error_count / len(recent_api_metrics) * 100
            if error_rate > 10:  # 错误率超过10%
                issues.append(f"API错误率过高: {error_rate:.1f}%")
        
        if issues:
            return {
                "status": "warning",
                "message": "发现性能问题",
                "issues": issues,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "healthy",
                "message": "系统运行正常",
                "timestamp": datetime.now().isoformat()
            }

# 全局监控实例
performance_monitor = PerformanceMonitor()

def get_monitor() -> PerformanceMonitor:
    """获取全局监控实例"""
    return performance_monitor

def start_monitoring(interval: float = 60.0):
    """启动监控"""
    performance_monitor.start_monitoring(interval)

def stop_monitoring():
    """停止监控"""
    performance_monitor.stop_monitoring()

def record_api_call(endpoint: str, method: str, status_code: int, 
                   response_time_ms: float, user_id: Optional[str] = None,
                   error_message: Optional[str] = None):
    """记录API调用"""
    performance_monitor.record_api_call(
        endpoint, method, status_code, response_time_ms, user_id, error_message
    )
