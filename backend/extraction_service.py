"""
Enhanced Timesheet Extraction Service with Real-Time Updates
Implements Phase 1 improvements: Parallel processing, WebSocket updates, Confidence scoring
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculate confidence scores for extracted timesheet fields"""
    
    @staticmethod
    def score_field(field_value: str, field_type: str) -> float:
        """
        Score individual field extraction confidence (0.0 to 1.0)
        
        Args:
            field_value: The extracted value
            field_type: Type of field (name, date, time, code, etc.)
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not field_value or field_value.strip() == "":
            return 0.0
        
        score = 0.5  # Base score for non-empty field
        
        if field_type == "name":
            # Names should have at least 2 parts and reasonable length
            parts = field_value.split()
            if len(parts) >= 2:
                score += 0.3
            if 3 <= len(field_value) <= 50:
                score += 0.2
            # Penalize if contains numbers or special chars
            if re.search(r'[0-9]', field_value):
                score -= 0.2
        
        elif field_type == "date":
            # Dates should match common patterns
            date_patterns = [
                r'\d{1,2}/\d{1,2}(/\d{2,4})?',  # 10/6 or 10/6/24
                r'\d{1,2}-\d{1,2}(-\d{2,4})?',  # 10-6 or 10-6-24
                r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)',  # Day names
                r'\d{4}-\d{2}-\d{2}'  # ISO format
            ]
            for pattern in date_patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    score += 0.5
                    break
        
        elif field_type == "time":
            # Times should match time patterns
            time_patterns = [
                r'\d{1,2}:\d{2}',  # 8:30 or 18:00
                r'\d{4}',  # Military time 1800
                r'\d{1,2}:\d{2}\s*(AM|PM)',  # 8:30 AM
            ]
            for pattern in time_patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    score += 0.5
                    break
        
        elif field_type == "service_code":
            # Service codes are usually 4-6 characters, alphanumeric
            if 3 <= len(field_value) <= 8:
                score += 0.3
            if re.match(r'^[A-Z0-9]+$', field_value.upper()):
                score += 0.2
        
        elif field_type == "signature":
            # Signature should be Yes/No or similar
            if field_value.lower() in ['yes', 'no', 'y', 'n', 'present', 'missing']:
                score += 0.5
        
        # Cap at 1.0
        return min(score, 1.0)
    
    @staticmethod
    def score_time_entry(entry: Dict) -> Tuple[float, Dict[str, float]]:
        """Score a complete time entry"""
        field_scores = {
            "date": ConfidenceScorer.score_field(entry.get("date", ""), "date"),
            "time_in": ConfidenceScorer.score_field(entry.get("time_in", ""), "time"),
            "time_out": ConfidenceScorer.score_field(entry.get("time_out", ""), "time"),
        }
        
        # Check logical consistency
        if entry.get("time_in") and entry.get("time_out"):
            # Both times present increases confidence
            field_scores["time_consistency"] = 0.2
        else:
            field_scores["time_consistency"] = 0.0
        
        # Overall entry score is average of field scores
        avg_score = sum(field_scores.values()) / len(field_scores)
        return avg_score, field_scores
    
    @staticmethod
    def score_employee_entry(emp_entry: Dict) -> Tuple[float, Dict]:
        """Score an employee entry with all time entries"""
        scores = {
            "employee_name": ConfidenceScorer.score_field(emp_entry.get("employee_name", ""), "name"),
            "service_code": ConfidenceScorer.score_field(emp_entry.get("service_code", ""), "service_code"),
            "signature": ConfidenceScorer.score_field(emp_entry.get("signature", ""), "signature"),
            "time_entries": []
        }
        
        # Score each time entry
        time_entries = emp_entry.get("time_entries", [])
        if time_entries:
            for entry in time_entries:
                entry_score, entry_details = ConfidenceScorer.score_time_entry(entry)
                scores["time_entries"].append({
                    "score": entry_score,
                    "details": entry_details
                })
            
            # Average time entry scores
            avg_time_entry_score = sum(e["score"] for e in scores["time_entries"]) / len(scores["time_entries"])
            scores["time_entries_avg"] = avg_time_entry_score
        else:
            scores["time_entries_avg"] = 0.0
        
        # Overall employee entry score
        overall_score = (
            scores["employee_name"] * 0.25 +
            scores["service_code"] * 0.15 +
            scores["signature"] * 0.10 +
            scores["time_entries_avg"] * 0.50
        )
        
        scores["overall"] = overall_score
        return overall_score, scores
    
    @staticmethod
    def score_extraction(extracted_data: Dict) -> Tuple[float, Dict]:
        """Score complete extraction result"""
        scores = {
            "client_name": ConfidenceScorer.score_field(extracted_data.get("client_name", ""), "name"),
            "employee_entries": []
        }
        
        # Score each employee entry
        employee_entries = extracted_data.get("employee_entries", [])
        if employee_entries:
            for emp_entry in employee_entries:
                emp_score, emp_details = ConfidenceScorer.score_employee_entry(emp_entry)
                scores["employee_entries"].append({
                    "score": emp_score,
                    "details": emp_details
                })
            
            # Average employee scores
            avg_emp_score = sum(e["score"] for e in scores["employee_entries"]) / len(scores["employee_entries"])
            scores["employee_entries_avg"] = avg_emp_score
        else:
            scores["employee_entries_avg"] = 0.0
        
        # Overall extraction score
        overall_score = (
            scores["client_name"] * 0.20 +
            scores["employee_entries_avg"] * 0.80
        )
        
        scores["overall"] = overall_score
        scores["recommendation"] = ConfidenceScorer.get_recommendation(overall_score)
        
        return overall_score, scores
    
    @staticmethod
    def get_recommendation(score: float) -> str:
        """Get action recommendation based on confidence score"""
        if score >= 0.95:
            return "auto_accept"
        elif score >= 0.80:
            return "review_recommended"
        elif score >= 0.60:
            return "manual_review_required"
        else:
            return "manual_entry_required"


class ExtractionProgress:
    """Track and broadcast extraction progress"""
    
    def __init__(self, timesheet_id: str, socket_manager=None):
        self.timesheet_id = timesheet_id
        self.socket_manager = socket_manager
        self.progress = {
            "timesheet_id": timesheet_id,
            "status": "starting",
            "progress_percent": 0,
            "current_step": "Initializing",
            "extracted_fields": {},
            "confidence_score": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def update(self, status: str = None, progress_percent: int = None, 
                     current_step: str = None, extracted_fields: Dict = None,
                     confidence_score: float = None):
        """Update progress and broadcast via WebSocket"""
        if status:
            self.progress["status"] = status
        if progress_percent is not None:
            self.progress["progress_percent"] = progress_percent
        if current_step:
            self.progress["current_step"] = current_step
        if extracted_fields:
            self.progress["extracted_fields"] = extracted_fields
        if confidence_score is not None:
            self.progress["confidence_score"] = confidence_score
        
        self.progress["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Broadcast via WebSocket if available
        if self.socket_manager:
            await self.socket_manager.broadcast_extraction_progress(self.progress)
        
        logger.info(f"Extraction progress: {self.progress['current_step']} - {self.progress['progress_percent']}%")
    
    async def complete(self, extracted_data: Dict, confidence_score: float, confidence_details: Dict):
        """Mark extraction as complete"""
        await self.update(
            status="completed",
            progress_percent=100,
            current_step="Extraction complete",
            extracted_fields=extracted_data,
            confidence_score=confidence_score
        )
        
        # Add confidence details
        self.progress["confidence_details"] = confidence_details
    
    async def error(self, error_message: str):
        """Mark extraction as failed"""
        await self.update(
            status="failed",
            current_step=f"Error: {error_message}"
        )
