"""
Data quality monitoring and validation for literature mining.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Container for extraction quality metrics."""
    total_records: int = 0
    valid_records: int = 0
    records_with_ph: int = 0
    records_with_temp: int = 0
    records_with_conc: int = 0
    records_with_all_params: int = 0
    validation_warnings: int = 0
    negated_records: int = 0
    comparison_records: int = 0
    high_confidence_records: int = 0
    avg_confidence: float = 0.0
    section_distribution: Dict[str, int] = None
    
    def __post_init__(self):
        if self.section_distribution is None:
            self.section_distribution = {}

@dataclass
class ExtractionReport:
    """Comprehensive extraction quality report."""
    timestamp: str
    source_info: Dict[str, Any]
    metrics: QualityMetrics
    warnings: List[str]
    recommendations: List[str]
    sample_records: List[Dict[str, Any]]

class QualityMonitor:
    """Monitor and validate extraction quality."""
    
    def __init__(self, output_dir: str = "quality_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.current_metrics = QualityMetrics()
        self.warnings = []
        self.recommendations = []
    
    def reset_metrics(self):
        """Reset metrics for new extraction session."""
        self.current_metrics = QualityMetrics()
        self.warnings = []
        self.recommendations = []
    
    def analyze_extraction_batch(self, records: List[Dict[str, Any]], source_info: Dict[str, Any] = None) -> ExtractionReport:
        """
        Analyze a batch of extraction records and generate quality report.
        
        Args:
            records: List of extraction records
            source_info: Information about the source (URLs, query, etc.)
            
        Returns:
            ExtractionReport with quality analysis
        """
        self.reset_metrics()
        
        if not records:
            self.warnings.append("No records extracted")
            self.recommendations.append("Check extraction patterns and source quality")
            return self._generate_report(source_info or {})
        
        # Analyze each record
        confidence_scores = []
        section_counts = {}
        
        for record in records:
            self._analyze_single_record(record, confidence_scores, section_counts)
        
        # Calculate aggregate metrics
        self.current_metrics.total_records = len(records)
        self.current_metrics.valid_records = len([r for r in records if self._is_valid_record(r)])
        self.current_metrics.avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        self.current_metrics.section_distribution = section_counts
        
        # Generate warnings and recommendations
        self._generate_warnings_and_recommendations()
        
        return self._generate_report(source_info or {}, records[:5])  # Include sample records
    
    def _analyze_single_record(self, record: Dict[str, Any], confidence_scores: List[float], section_counts: Dict[str, int]):
        """Analyze a single extraction record."""
        params = record.get('parameters', {})
        
        # Count parameter availability
        # Handle both dict and Pydantic model cases
        if hasattr(params, 'pH'):
            # Pydantic model case
            if params.pH is not None:
                self.current_metrics.records_with_ph += 1
            if params.temperature_c is not None:
                self.current_metrics.records_with_temp += 1
            if params.concentration_mg_ml is not None:
                self.current_metrics.records_with_conc += 1
            
            # Check if all parameters are present
            if all(getattr(params, p) is not None for p in ['pH', 'temperature_c', 'concentration_mg_ml']):
                self.current_metrics.records_with_all_params += 1
        else:
            # Dict case (fallback)
            if params.get('pH') is not None:
                self.current_metrics.records_with_ph += 1
            if params.get('temperature_c') is not None:
                self.current_metrics.records_with_temp += 1
            if params.get('concentration_mg_ml') is not None:
                self.current_metrics.records_with_conc += 1
            
            # Check if all parameters are present
            if all(params.get(p) is not None for p in ['pH', 'temperature_c', 'concentration_mg_ml']):
                self.current_metrics.records_with_all_params += 1
        
        # Analyze confidence
        confidence = record.get('confidence', 0.0)
        confidence_scores.append(confidence)
        if confidence >= 0.7:
            self.current_metrics.high_confidence_records += 1
        
        # Check for validation warnings in parameter notes
        if hasattr(params, 'raw_context'):
            raw_context = params.raw_context or ''
        else:
            raw_context = params.get('raw_context', '') if isinstance(params, dict) else ''
        if 'WARNING' in raw_context:
            self.current_metrics.validation_warnings += 1
        
        # Analyze context features (if available)
        context_info = record.get('context_analysis', {})
        if context_info.get('has_negation', False):
            self.current_metrics.negated_records += 1
        if context_info.get('comparison_info', {}).get('has_comparison', False):
            self.current_metrics.comparison_records += 1
        
        # Track section distribution
        section_weight = context_info.get('section_weight', 0.5)
        if section_weight >= 0.9:
            section_type = 'methods_results'
        elif section_weight >= 0.6:
            section_type = 'discussion_abstract'
        else:
            section_type = 'introduction_other'
        
        section_counts[section_type] = section_counts.get(section_type, 0) + 1
    
    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """Check if a record is considered valid."""
        params = record.get('parameters', {})
        
        # Must have at least one parameter and outcome
        if hasattr(params, 'pH'):
            # Pydantic model case
            has_param = any(getattr(params, p) is not None for p in ['pH', 'temperature_c', 'concentration_mg_ml'])
        else:
            # Dict case
            has_param = any(params.get(p) is not None for p in ['pH', 'temperature_c', 'concentration_mg_ml'])
        
        has_outcome = record.get('outcome_label') is not None
        has_reasonable_confidence = record.get('confidence', 0.0) >= 0.3
        
        return has_param and has_outcome and has_reasonable_confidence
    
    def _generate_warnings_and_recommendations(self):
        """Generate warnings and recommendations based on metrics."""
        metrics = self.current_metrics
        
        # Parameter coverage warnings
        if metrics.records_with_ph / metrics.total_records < 0.3:
            self.warnings.append(f"Low pH extraction rate: {metrics.records_with_ph}/{metrics.total_records} ({metrics.records_with_ph/metrics.total_records:.1%})")
            self.recommendations.append("Expand pH-related regex patterns")
        
        if metrics.records_with_temp / metrics.total_records < 0.3:
            self.warnings.append(f"Low temperature extraction rate: {metrics.records_with_temp}/{metrics.total_records} ({metrics.records_with_temp/metrics.total_records:.1%})")
            self.recommendations.append("Add more temperature expression patterns")
        
        if metrics.records_with_conc / metrics.total_records < 0.3:
            self.warnings.append(f"Low concentration extraction rate: {metrics.records_with_conc}/{metrics.total_records} ({metrics.records_with_conc/metrics.total_records:.1%})")
            self.recommendations.append("Expand concentration unit patterns")
        
        # Complete parameter sets
        if metrics.records_with_all_params / metrics.total_records < 0.1:
            self.warnings.append(f"Very few records with all parameters: {metrics.records_with_all_params}/{metrics.total_records} ({metrics.records_with_all_params/metrics.total_records:.1%})")
            self.recommendations.append("Improve co-occurrence detection of parameters")
        
        # Confidence analysis
        if metrics.avg_confidence < 0.5:
            self.warnings.append(f"Low average confidence: {metrics.avg_confidence:.2f}")
            self.recommendations.append("Review confidence scoring algorithm")
        
        if metrics.high_confidence_records / metrics.total_records < 0.2:
            self.warnings.append(f"Few high-confidence records: {metrics.high_confidence_records}/{metrics.total_records} ({metrics.high_confidence_records/metrics.total_records:.1%})")
            self.recommendations.append("Improve extraction patterns for higher precision")
        
        # Validation warnings
        if metrics.validation_warnings > metrics.total_records * 0.1:
            self.warnings.append(f"Many validation warnings: {metrics.validation_warnings}")
            self.recommendations.append("Review parameter validation ranges")
        
        # Context analysis
        if metrics.negated_records > metrics.total_records * 0.3:
            self.warnings.append(f"High negation rate: {metrics.negated_records}/{metrics.total_records} ({metrics.negated_records/metrics.total_records:.1%})")
            self.recommendations.append("Improve negation handling in extraction logic")
        
        # Section distribution
        low_quality_sections = metrics.section_distribution.get('introduction_other', 0)
        if low_quality_sections > metrics.total_records * 0.5:
            self.warnings.append(f"Many extractions from low-quality sections: {low_quality_sections}")
            self.recommendations.append("Implement section filtering to focus on Methods/Results")
    
    def _generate_report(self, source_info: Dict[str, Any], sample_records: List[Dict[str, Any]] = None) -> ExtractionReport:
        """Generate comprehensive extraction report."""
        return ExtractionReport(
            timestamp=datetime.now().isoformat(),
            source_info=source_info,
            metrics=self.current_metrics,
            warnings=self.warnings.copy(),
            recommendations=self.recommendations.copy(),
            sample_records=sample_records or []
        )
    
    def save_report(self, report: ExtractionReport, filename: Optional[str] = None) -> Path:
        """Save extraction report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Convert report to dictionary for JSON serialization
        # Convert sample records to JSON-serializable format
        serializable_records = []
        for record in report.sample_records:
            serializable_record = record.copy()
            # Convert ExperimentalParameters to dict if present
            if 'parameters' in serializable_record and hasattr(serializable_record['parameters'], 'model_dump'):
                serializable_record['parameters'] = serializable_record['parameters'].model_dump()
            elif 'parameters' in serializable_record and hasattr(serializable_record['parameters'], '__dict__'):
                serializable_record['parameters'] = serializable_record['parameters'].__dict__
            serializable_records.append(serializable_record)
        
        report_dict = {
            'timestamp': report.timestamp,
            'source_info': report.source_info,
            'metrics': {
                'total_records': report.metrics.total_records,
                'valid_records': report.metrics.valid_records,
                'records_with_ph': report.metrics.records_with_ph,
                'records_with_temp': report.metrics.records_with_temp,
                'records_with_conc': report.metrics.records_with_conc,
                'records_with_all_params': report.metrics.records_with_all_params,
                'validation_warnings': report.metrics.validation_warnings,
                'negated_records': report.metrics.negated_records,
                'comparison_records': report.metrics.comparison_records,
                'high_confidence_records': report.metrics.high_confidence_records,
                'avg_confidence': report.metrics.avg_confidence,
                'section_distribution': report.metrics.section_distribution,
            },
            'warnings': report.warnings,
            'recommendations': report.recommendations,
            'sample_records': serializable_records
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Quality report saved to {filepath}")
        return filepath
    
    def print_summary(self, report: ExtractionReport):
        """Print a summary of the extraction quality report."""
        print("\n" + "="*60)
        print("EXTRACTION QUALITY REPORT")
        print("="*60)
        print(f"Timestamp: {report.timestamp}")
        print(f"Source: {report.source_info.get('query', 'Unknown')}")
        print(f"Total URLs: {report.source_info.get('total_urls', 'Unknown')}")
        
        print("\nMETRICS:")
        print(f"  Total records: {report.metrics.total_records}")
        print(f"  Valid records: {report.metrics.valid_records} ({report.metrics.valid_records/max(1,report.metrics.total_records):.1%})")
        print(f"  Average confidence: {report.metrics.avg_confidence:.2f}")
        print(f"  High confidence (≥0.7): {report.metrics.high_confidence_records} ({report.metrics.high_confidence_records/max(1,report.metrics.total_records):.1%})")
        
        print("\nPARAMETER COVERAGE:")
        print(f"  pH: {report.metrics.records_with_ph} ({report.metrics.records_with_ph/max(1,report.metrics.total_records):.1%})")
        print(f"  Temperature: {report.metrics.records_with_temp} ({report.metrics.records_with_temp/max(1,report.metrics.total_records):.1%})")
        print(f"  Concentration: {report.metrics.records_with_conc} ({report.metrics.records_with_conc/max(1,report.metrics.total_records):.1%})")
        print(f"  All parameters: {report.metrics.records_with_all_params} ({report.metrics.records_with_all_params/max(1,report.metrics.total_records):.1%})")
        
        if report.warnings:
            print(f"\nWARNINGS ({len(report.warnings)}):")
            for warning in report.warnings:
                print(f"  ⚠️  {warning}")
        
        if report.recommendations:
            print(f"\nRECOMMENDATIONS ({len(report.recommendations)}):")
            for rec in report.recommendations:
                print(f"  💡 {rec}")
        
        print("="*60)

# Global quality monitor instance
quality_monitor = QualityMonitor()