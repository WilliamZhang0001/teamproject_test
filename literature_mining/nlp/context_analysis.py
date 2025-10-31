"""
Context analysis module for enhanced NLP extraction.
Handles negation detection, comparison analysis, and section weighting.
"""

from typing import Dict, List, Tuple, Optional
import re
from .regex_patterns import NEGATION_PATTERNS, COMPARISON_PATTERNS, SECTION_PATTERNS

class ContextAnalyzer:
    """Analyzes textual context for better extraction quality."""
    
    def __init__(self):
        self.negation_window = 12  # Words to look for negation (expanded from 5)
        self.comparison_window = 10  # Words to look for comparisons
        self.parameter_outcome_window = 30  # Maximum words between parameter and outcome for association
        # Cache for section analysis to avoid repeated computation
        self._section_cache = {}
    
    def detect_negation(self, text: str, target_pos: int) -> bool:
        """
        Detect if a target position in text is negated.
        
        Args:
            text: Input text
            target_pos: Character position of target term
            
        Returns:
            True if target is likely negated
        """
        # Extract window around target
        words = text.split()
        char_to_word = self._build_char_to_word_map(text, words)
        
        if target_pos not in char_to_word:
            return False
        
        target_word_idx = char_to_word[target_pos]
        # Expanded window: check both before and after target
        start_idx = max(0, target_word_idx - self.negation_window)
        end_idx = min(len(words), target_word_idx + self.negation_window + 1)
        
        window_text = ' '.join(words[start_idx:end_idx])
        
        # Check for negation patterns
        for pattern in NEGATION_PATTERNS:
            if pattern.search(window_text):
                return True
        
        return False
    
    def detect_comparison(self, text: str) -> Dict[str, any]:
        """
        Detect comparative statements in text.
        
        Returns:
            Dictionary with comparison information
        """
        comparison_info = {
            'has_comparison': False,
            'comparison_type': None,
            'comparison_terms': [],
            'confidence': 0.0
        }
        
        matches = []
        for pattern in COMPARISON_PATTERNS:
            for match in pattern.finditer(text):
                matches.append({
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end(),
                    'pattern': pattern.pattern
                })
        
        if matches:
            comparison_info['has_comparison'] = True
            comparison_info['comparison_terms'] = [m['text'] for m in matches]
            comparison_info['confidence'] = min(1.0, len(matches) * 0.3)
            
            # Determine comparison type
            comparative_text = ' '.join([m['text'] for m in matches]).lower()
            if any(word in comparative_text for word in ['more', 'higher', 'greater', 'increase', 'improve', 'enhance']):
                comparison_info['comparison_type'] = 'positive'
            elif any(word in comparative_text for word in ['less', 'lower', 'smaller', 'decrease', 'reduce']):
                comparison_info['comparison_type'] = 'negative'
            else:
                comparison_info['comparison_type'] = 'neutral'
        
        return comparison_info
    
    def identify_section(self, text: str) -> Dict[str, float]:
        """
        Identify document section and assign weights.
        
        Returns:
            Dictionary mapping section types to confidence scores
        """
        section_scores = {}
        
        for section_name, pattern in SECTION_PATTERNS.items():
            matches = list(pattern.finditer(text))
            if matches:
                # Score based on number of matches and position
                score = len(matches) * 0.3
                # Boost score if section appears early in text
                if matches[0].start() < len(text) * 0.2:
                    score *= 1.5
                section_scores[section_name] = min(1.0, score)
        
        return section_scores
    
    def get_section_weight(self, text: str) -> float:
        """
        Get overall weight for text based on section identification.
        
        Section weights (higher = more reliable):
        - Results: 1.0
        - Methods: 0.9
        - Discussion: 0.7
        - Abstract: 0.6
        - Introduction: 0.3
        """
        # Check cache first (for short texts like sentences)
        if text in self._section_cache:
            return self._section_cache[text]
        
        section_weights = {
            'results': 1.0,
            'methods': 0.9,
            'discussion': 0.7,
            'abstract': 0.6,
            'introduction': 0.3
        }
        
        section_scores = self.identify_section(text)
        
        if not section_scores:
            weight = 0.5  # Default weight for unidentified sections
        else:
            # Weighted average of section scores
            total_weight = 0.0
            total_confidence = 0.0
            
            for section, confidence in section_scores.items():
                if section in section_weights:
                    total_weight += section_weights[section] * confidence
                    total_confidence += confidence
            
            if total_confidence > 0:
                weight = total_weight / total_confidence
            else:
                weight = 0.5
        
        # Cache result for sentences
        if len(text) < 500:  # Only cache short texts
            if len(self._section_cache) < 1000:
                self._section_cache[text] = weight
        
        return weight
    
    def analyze_sentence_context(self, sentence: str) -> Dict[str, any]:
        """
        Comprehensive context analysis for a sentence.
        
        Returns:
            Dictionary with all context analysis results
        """
        context = {
            'section_weight': self.get_section_weight(sentence),
            'comparison_info': self.detect_comparison(sentence),
            'has_negation': False,
            'reliability_score': 0.0
        }
        
        # Check for negation around stability terms
        stability_terms = ['stable', 'stability', 'unstable', 'denatur', 'aggregat', 'precipitat']
        for term in stability_terms:
            pattern = re.compile(rf'\b{term}\w*', re.IGNORECASE)
            for match in pattern.finditer(sentence):
                if self.detect_negation(sentence, match.start()):
                    context['has_negation'] = True
                    break
        
        # Calculate overall reliability score
        reliability = context['section_weight']
        
        # Reduce reliability for negated statements (they're still useful but need careful handling)
        if context['has_negation']:
            reliability *= 0.7
        
        # Adjust for comparisons (can be valuable but need context)
        if context['comparison_info']['has_comparison']:
            reliability *= 0.8
        
        context['reliability_score'] = reliability
        
        return context
    
    def _build_char_to_word_map(self, text: str, words: List[str]) -> Dict[int, int]:
        """Build mapping from character positions to word indices."""
        char_to_word = {}
        char_pos = 0
        
        for word_idx, word in enumerate(words):
            # Find word in text starting from char_pos
            word_start = text.find(word, char_pos)
            if word_start != -1:
                for i in range(word_start, word_start + len(word)):
                    char_to_word[i] = word_idx
                char_pos = word_start + len(word)
        
        return char_to_word
    
    def calculate_parameter_outcome_association(self, sentence: str) -> Dict[str, any]:
        """
        Calculate association score between parameters and outcomes in a sentence.
        
        Higher score means parameter and outcome are more likely related.
        
        Args:
            sentence: Sentence to analyze
            
        Returns:
            Dictionary with association information and score
        """
        # Parameter indicators
        parameter_patterns = [
            r'\bpH\s*[=:~\s]*\d+',  # pH values
            r'\d+\s*°?\s*C',  # Temperature
            r'\d+\s*(?:mg/mL|mM|μM|µM|nM|pM|%)',  # Concentration
            r'\bionic\s*strength',
            r'\bpressure\s*\d+',
            r'\bshear\s*rate',
        ]
        
        # Outcome indicators
        outcome_patterns = [
            r'\b(?:stable|stability|unstable)',
            r'\b(?:denatur|aggregat|precipitat)',
            r'\b(?:soluble|insoluble|solubility)',
            r'\b(?:activity|active|inactive)',
        ]
        
        # Find all parameter and outcome positions
        param_positions = []
        outcome_positions = []
        
        words = sentence.split()
        char_pos = 0
        
        # Find parameters
        for pattern_str in parameter_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(sentence):
                word_idx = len(sentence[:match.start()].split())
                param_positions.append((word_idx, match.start(), match.end()))
        
        # Find outcomes
        for pattern_str in outcome_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(sentence):
                word_idx = len(sentence[:match.start()].split())
                outcome_positions.append((word_idx, match.start(), match.end()))
        
        # Calculate association score
        association_score = 0.0
        min_distance = float('inf')
        associated_pairs = []
        
        if param_positions and outcome_positions:
            # Calculate minimum word distance between any parameter and outcome
            for p_word_idx, p_start, p_end in param_positions:
                for o_word_idx, o_start, o_end in outcome_positions:
                    distance = abs(o_word_idx - p_word_idx)
                    min_distance = min(min_distance, distance)
                    if distance <= self.parameter_outcome_window:
                        # Calculate score based on distance (closer = higher score)
                        score = max(0, 1.0 - (distance / self.parameter_outcome_window))
                        association_score = max(association_score, score)
                        associated_pairs.append({
                            'param_pos': p_word_idx,
                            'outcome_pos': o_word_idx,
                            'distance': distance,
                            'score': score
                        })
        
        return {
            'has_association': len(associated_pairs) > 0,
            'association_score': association_score,
            'min_distance': min_distance if min_distance != float('inf') else None,
            'num_params': len(param_positions),
            'num_outcomes': len(outcome_positions),
            'associated_pairs': associated_pairs
        }
    
    def filter_high_quality_sentences(self, sentences: List[str], min_reliability: float = 0.5) -> List[Tuple[str, float]]:
        """
        Filter sentences based on context analysis and parameter-outcome association.
        
        Enhanced version that combines reliability and association scores.
        
        Args:
            sentences: List of sentences to analyze
            min_reliability: Minimum reliability score to keep (lowered from 0.6 to 0.5)
            
        Returns:
            List of (sentence, combined_score) tuples, sorted by score
        """
        filtered = []
        
        import logging
        logger = logging.getLogger(__name__)
        
        total = len(sentences)
        # Performance optimization: limit processing for very long texts
        max_sentences = 1000  # Process max 1000 sentences per text
        if total > max_sentences:
            logger.warning(f"Large text detected ({total} sentences), processing first {max_sentences} sentences only")
            sentences = sentences[:max_sentences]
            total = max_sentences
        
        # Show progress for long processing
        show_progress = total > 100
        progress_interval = max(1, total // 20)  # Show ~20 progress updates
        
        for idx, sentence in enumerate(sentences):
            try:
                context = self.analyze_sentence_context(sentence)
                reliability = context['reliability_score']
                
                # Calculate parameter-outcome association
                association_info = self.calculate_parameter_outcome_association(sentence)
                
                # Combined score: reliability + association bonus
                combined_score = reliability
                if association_info['has_association']:
                    # Boost score if parameters and outcomes are associated
                    combined_score += association_info['association_score'] * 0.3
                    combined_score = min(1.0, combined_score)  # Cap at 1.0
                
                if combined_score >= min_reliability:
                    filtered.append((sentence, combined_score, {
                        'reliability': reliability,
                        'association_score': association_info['association_score'],
                        'has_association': association_info['has_association']
                    }))
                
                # Show progress for long texts (use print for visibility)
                if show_progress and idx > 0 and idx % progress_interval == 0:
                    progress_pct = (idx / total) * 100
                    print(f"  ⏳ 上下文分析进度: {idx}/{total} ({progress_pct:.1f}%)...", end='\r', flush=True)
            except Exception as e:
                logger.warning(f"Error analyzing sentence {idx}: {e}")
                # Continue processing other sentences
                continue
        
        if show_progress:
            print(f"  ✅ 上下文分析完成: {total}/{total} (100%){' ' * 20}")  # Clear line
        
        # Sort by combined score (descending)
        filtered.sort(key=lambda x: x[1], reverse=True)
        
        # Return in format: (sentence, score) for backward compatibility
        return [(sent, score) for sent, score, _ in filtered]

# Global context analyzer instance
context_analyzer = ContextAnalyzer()