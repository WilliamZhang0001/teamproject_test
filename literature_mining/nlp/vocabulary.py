"""
Professional vocabulary and synonym mapping for biomolecule stability analysis.
"""

from typing import Dict, List, Set
import re

# Biomolecule type synonyms
BIOMOLECULE_SYNONYMS = {
    'protein': ['protein', 'polypeptide', 'enzyme', 'antibody', 'immunoglobulin', 'globulin'],
    'peptide': ['peptide', 'oligopeptide', 'dipeptide', 'tripeptide', 'tetrapeptide'],
    'nucleic_acid': ['DNA', 'RNA', 'nucleic acid', 'oligonucleotide', 'polynucleotide'],
    'polysaccharide': ['polysaccharide', 'carbohydrate', 'glycan', 'oligosaccharide'],
    'lipid': ['lipid', 'phospholipid', 'liposome', 'fatty acid'],
}

# Stability-related terms with semantic categories
STABILITY_TERMS = {
    'positive_stability': [
        'stable', 'stability', 'stabilize', 'stabilization', 'stabilized',
        'maintain', 'preserve', 'retain', 'conserve', 'protect',
        'thermostable', 'heat-stable', 'temperature-stable',
        'long-term stable', 'storage stable', 'shelf-stable',
        'conformationally stable', 'structurally stable',
        'native', 'folded', 'active', 'functional', 'intact'
    ],
    'negative_stability': [
        'unstable', 'instability', 'destabilize', 'destabilization',
        'denature', 'denaturation', 'denatured', 'unfolding', 'unfold',
        'aggregate', 'aggregation', 'aggregated', 'clumping',
        'precipitate', 'precipitation', 'precipitated',
        'degrade', 'degradation', 'degraded', 'breakdown',
        'hydrolyze', 'hydrolysis', 'proteolysis', 'oxidation',
        'fibril', 'fibrillation', 'amyloid', 'gelation',
        'inactive', 'inactivate', 'inactivation', 'loss of activity'
    ],
    'solubility_positive': [
        'soluble', 'solubility', 'solubilize', 'solubilization',
        'dissolve', 'dissolved', 'dissolution', 'dispersed',
        'clear solution', 'transparent', 'homogeneous'
    ],
    'solubility_negative': [
        'insoluble', 'insolubility', 'precipitate', 'precipitation',
        'turbid', 'turbidity', 'cloudy', 'opaque', 'sediment',
        'phase separation', 'crystallize', 'crystallization'
    ]
}

# Experimental condition terms
CONDITION_TERMS = {
    'ph_descriptors': [
        'acidic', 'basic', 'alkaline', 'neutral', 'physiological pH',
        'low pH', 'high pH', 'pH stress', 'pH shift', 'pH change'
    ],
    'temperature_descriptors': [
        'room temperature', 'RT', 'ambient temperature',
        'cold', 'chilled', 'frozen', 'ice-cold',
        'heated', 'hot', 'elevated temperature', 'high temperature',
        'thermal stress', 'heat shock', 'temperature stress',
        'physiological temperature', 'body temperature'
    ],
    'concentration_descriptors': [
        'dilute', 'concentrated', 'high concentration', 'low concentration',
        'saturated', 'supersaturated', 'subsaturated'
    ]
}

# Buffer and additive terms
BUFFER_ADDITIVES = {
    'buffers': [
        'Tris', 'HEPES', 'phosphate', 'PBS', 'bicarbonate',
        'acetate', 'citrate', 'glycine', 'bis-tris', 'MOPS'
    ],
    'salts': [
        'NaCl', 'KCl', 'MgCl2', 'CaCl2', 'sodium chloride',
        'potassium chloride', 'magnesium chloride', 'calcium chloride'
    ],
    'stabilizers': [
        'glycerol', 'sucrose', 'trehalose', 'mannitol', 'sorbitol',
        'PEG', 'polyethylene glycol', 'BSA', 'albumin',
        'DTT', 'TCEP', 'reducing agent', 'antioxidant'
    ],
    'denaturants': [
        'urea', 'guanidine', 'SDS', 'detergent', 'chaotrope',
        'organic solvent', 'alcohol', 'acetonitrile'
    ]
}

# Measurement and analysis terms
ANALYSIS_TERMS = {
    'spectroscopy': [
        'UV', 'fluorescence', 'CD', 'circular dichroism',
        'NMR', 'IR', 'Raman', 'absorbance', 'emission'
    ],
    'chromatography': [
        'HPLC', 'SEC', 'size exclusion', 'ion exchange',
        'reverse phase', 'gel filtration', 'chromatography'
    ],
    'other_methods': [
        'DLS', 'dynamic light scattering', 'SDS-PAGE',
        'mass spectrometry', 'MS', 'gel electrophoresis',
        'turbidity', 'viscosity', 'activity assay'
    ]
}

class VocabularyMatcher:
    """Enhanced vocabulary matching with synonym support."""
    
    def __init__(self):
        self.synonym_map = self._build_synonym_map()
        self.category_patterns = self._build_category_patterns()
        # Cache for category matching results
        self._category_cache = {}
    
    def _build_synonym_map(self) -> Dict[str, str]:
        """Build a mapping from terms to their canonical forms."""
        synonym_map = {}
        
        # Add biomolecule synonyms
        for canonical, synonyms in BIOMOLECULE_SYNONYMS.items():
            for synonym in synonyms:
                synonym_map[synonym.lower()] = canonical
        
        # Add stability term categories
        for category, terms in STABILITY_TERMS.items():
            for term in terms:
                synonym_map[term.lower()] = category
        
        return synonym_map
    
    def _build_category_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build regex patterns for each category."""
        patterns = {}
        
        all_terms = {**STABILITY_TERMS, **CONDITION_TERMS, **BUFFER_ADDITIVES, **ANALYSIS_TERMS}
        
        for category, terms in all_terms.items():
            category_patterns = []
            for term in terms:
                # Escape special regex characters and create word boundary pattern
                escaped_term = re.escape(term)
                pattern = re.compile(rf"\b{escaped_term}\b", re.IGNORECASE)
                category_patterns.append(pattern)
            patterns[category] = category_patterns
        
        return patterns
    
    def normalize_term(self, term: str) -> str:
        """Normalize a term to its canonical form."""
        return self.synonym_map.get(term.lower(), term.lower())
    
    def find_categories(self, text: str) -> Dict[str, List[str]]:
        """Find all category matches in text."""
        # Check cache first
        if text in self._category_cache:
            return self._category_cache[text]
        
        matches = {}
        
        # Optimize: only check stability categories, not all categories
        stability_category_patterns = {
            cat: patterns for cat, patterns in self.category_patterns.items()
            if cat in ['positive_stability', 'negative_stability', 'solubility_positive', 'solubility_negative']
        }
        
        for category, patterns in stability_category_patterns.items():
            category_matches = []
            for pattern in patterns:
                for match in pattern.finditer(text):
                    category_matches.append(match.group(0))
            if category_matches:
                matches[category] = list(set(category_matches))  # Remove duplicates
        
        # Cache result (limit cache size to prevent memory issues)
        if len(self._category_cache) < 1000:
            self._category_cache[text] = matches
        
        return matches
    
    def is_stability_related(self, text: str) -> bool:
        """Check if text contains stability-related terms."""
        # Fast check using simple keywords to avoid expensive regex scanning
        text_lower = text.lower()
        keywords = ['stable', 'stability', 'denatur', 'aggregat', 'precipitat', 
                   'soluble', 'insoluble', 'solubility', 'unfold']
        return any(kw in text_lower for kw in keywords)
    
    def get_stability_polarity(self, text: str) -> str:
        """Determine if stability context is positive, negative, or neutral."""
        # Fast check using simple keywords
        text_lower = text.lower()
        
        positive_terms = ['stable', 'stabilize', 'maintain', 'preserve', 'soluble']
        negative_terms = ['unstable', 'denatur', 'aggregat', 'precipitat', 'insoluble']
        
        has_positive = any(term in text_lower for term in positive_terms)
        has_negative = any(term in text_lower for term in negative_terms)
        
        if has_positive and not has_negative:
            return 'positive'
        elif has_negative and not has_positive:
            return 'negative'
        elif has_positive and has_negative:
            return 'mixed'
        else:
            return 'neutral'

# Global vocabulary matcher instance
vocab_matcher = VocabularyMatcher()