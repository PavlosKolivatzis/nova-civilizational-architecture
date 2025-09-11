"""
Flow Metrics - Adaptive Connections Monitoring

Provides Prometheus-style metrics for adaptive link weight, frequency, and performance tracking.
Integrates with existing NOVA metrics infrastructure.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from .adaptive_connections import adaptive_link_registry


class FlowMetrics:
    """Metrics collection for Flow Fabric adaptive connections"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.last_collection_time = 0.0
    
    def collect_adaptive_link_metrics(self) -> Dict[str, Any]:
        """
        Collect current adaptive link metrics in Prometheus format.
        
        Returns metrics that can be exposed via /metrics endpoint:
        - adaptive_link_weight{contract="CONTRACT@1"}
        - adaptive_link_frequency{contract="CONTRACT@1"}  
        - adaptive_link_sends_total{contract="CONTRACT@1"}
        - adaptive_link_sends_throttled{contract="CONTRACT@1"}
        - adaptive_link_response_time_avg{contract="CONTRACT@1"}
        - adaptive_link_adjustments_total{contract="CONTRACT@1", type="weight|frequency"}
        """
        current_time = time.time()
        all_link_metrics = adaptive_link_registry.get_all_metrics()
        
        prometheus_metrics = {
            "adaptive_link_weight": {},
            "adaptive_link_frequency": {},
            "adaptive_link_sends_total": {},
            "adaptive_link_sends_throttled": {},
            "adaptive_link_response_time_avg": {},
            "adaptive_link_weight_adjustments_total": {},
            "adaptive_link_frequency_adjustments_total": {},
            "adaptive_link_adaptation_enabled": {}
        }
        
        for link_metrics in all_link_metrics:
            contract = link_metrics["contract_name"]
            
            # Core adaptive metrics
            prometheus_metrics["adaptive_link_weight"][contract] = link_metrics["current_weight"]
            prometheus_metrics["adaptive_link_frequency"][contract] = link_metrics["current_frequency"]
            
            # Volume metrics
            prometheus_metrics["adaptive_link_sends_total"][contract] = link_metrics["sends_total"]
            prometheus_metrics["adaptive_link_sends_throttled"][contract] = link_metrics["sends_throttled"]
            
            # Performance metrics
            prometheus_metrics["adaptive_link_response_time_avg"][contract] = link_metrics["average_response_time"]
            
            # Adjustment tracking
            prometheus_metrics["adaptive_link_weight_adjustments_total"][contract] = link_metrics["weight_adjustments"]
            prometheus_metrics["adaptive_link_frequency_adjustments_total"][contract] = link_metrics["frequency_adjustments"]
            
            # Feature flag status
            prometheus_metrics["adaptive_link_adaptation_enabled"][contract] = 1 if link_metrics["adaptation_enabled"] else 0
        
        # Add collection metadata
        collection_record = {
            "timestamp": current_time,
            "collection_duration": current_time - self.last_collection_time,
            "links_count": len(all_link_metrics),
            "metrics": prometheus_metrics
        }
        
        self.metrics_history.append(collection_record)
        self.last_collection_time = current_time
        
        # Keep only last 100 collections for memory management
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        return prometheus_metrics
    
    def get_flow_health_summary(self) -> Dict[str, Any]:
        """
        Get high-level flow health summary for /health endpoint integration.
        
        Provides overview of adaptive connection status and performance.
        """
        all_link_metrics = adaptive_link_registry.get_all_metrics()
        
        if not all_link_metrics:
            return {
                "adaptive_connections_active": False,
                "links_count": 0,
                "status": "no_links"
            }
        
        # Calculate summary statistics
        total_sends = sum(m["sends_total"] for m in all_link_metrics)
        total_throttled = sum(m["sends_throttled"] for m in all_link_metrics)
        total_adjustments = sum(m["weight_adjustments"] + m["frequency_adjustments"] for m in all_link_metrics)
        
        adaptation_enabled_count = sum(1 for m in all_link_metrics if m["adaptation_enabled"])
        
        avg_weight = sum(m["current_weight"] for m in all_link_metrics) / len(all_link_metrics)
        avg_frequency = sum(m["current_frequency"] for m in all_link_metrics) / len(all_link_metrics)
        avg_response_time = sum(m["average_response_time"] for m in all_link_metrics if m["average_response_time"] > 0)
        if avg_response_time > 0:
            response_count = sum(1 for m in all_link_metrics if m["average_response_time"] > 0)
            avg_response_time = avg_response_time / response_count if response_count > 0 else 0
        
        # Determine health status
        throttle_rate = total_throttled / total_sends if total_sends > 0 else 0
        
        if throttle_rate > 0.5:
            status = "high_throttling"
        elif total_adjustments > len(all_link_metrics) * 10:  # More than 10 adjustments per link
            status = "high_adaptation"
        elif adaptation_enabled_count == 0:
            status = "adaptation_disabled"
        else:
            status = "healthy"
        
        return {
            "adaptive_connections_active": True,
            "links_count": len(all_link_metrics),
            "adaptation_enabled_links": adaptation_enabled_count,
            "total_sends": total_sends,
            "total_throttled": total_throttled,
            "throttle_rate": round(throttle_rate, 3),
            "total_adjustments": total_adjustments,
            "average_weight": round(avg_weight, 2),
            "average_frequency": round(avg_frequency, 2),
            "average_response_time_ms": round(avg_response_time * 1000, 1),
            "status": status,
            "contracts_tracked": [m["contract_name"] for m in all_link_metrics]
        }
    
    def get_contract_metrics(self, contract_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for specific contract"""
        all_metrics = adaptive_link_registry.get_all_metrics()
        
        for metrics in all_metrics:
            if metrics["contract_name"] == contract_name:
                return metrics
        
        return None
    
    def get_metrics_for_prometheus(self) -> str:
        """
        Format metrics for Prometheus scraping.
        
        Returns metrics in Prometheus text format for /metrics endpoint.
        """
        prometheus_metrics = self.collect_adaptive_link_metrics()
        lines = []
        
        # Add help and type information
        lines.append("# HELP adaptive_link_weight Current weight for adaptive contract link")
        lines.append("# TYPE adaptive_link_weight gauge")
        
        for contract, value in prometheus_metrics["adaptive_link_weight"].items():
            lines.append(f'adaptive_link_weight{{contract="{contract}"}} {value}')
        
        lines.append("# HELP adaptive_link_frequency Current frequency for adaptive contract link")
        lines.append("# TYPE adaptive_link_frequency gauge")
        
        for contract, value in prometheus_metrics["adaptive_link_frequency"].items():
            lines.append(f'adaptive_link_frequency{{contract="{contract}"}} {value}')
        
        lines.append("# HELP adaptive_link_sends_total Total sends through adaptive link")
        lines.append("# TYPE adaptive_link_sends_total counter")
        
        for contract, value in prometheus_metrics["adaptive_link_sends_total"].items():
            lines.append(f'adaptive_link_sends_total{{contract="{contract}"}} {value}')
        
        lines.append("# HELP adaptive_link_sends_throttled Total throttled sends through adaptive link")
        lines.append("# TYPE adaptive_link_sends_throttled counter")
        
        for contract, value in prometheus_metrics["adaptive_link_sends_throttled"].items():
            lines.append(f'adaptive_link_sends_throttled{{contract="{contract}"}} {value}')
        
        lines.append("# HELP adaptive_link_response_time_avg Average response time for adaptive link")
        lines.append("# TYPE adaptive_link_response_time_avg gauge")
        
        for contract, value in prometheus_metrics["adaptive_link_response_time_avg"].items():
            lines.append(f'adaptive_link_response_time_avg{{contract="{contract}"}} {value}')
        
        return '\n'.join(lines)


# Global metrics instance
flow_metrics = FlowMetrics()


def get_flow_metrics() -> FlowMetrics:
    """Get global flow metrics instance"""
    return flow_metrics