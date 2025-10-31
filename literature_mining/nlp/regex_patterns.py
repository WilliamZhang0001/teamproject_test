import re

# Enhanced numeric patterns - support scientific notation, thousand separators, fractions
# 支持科学计数法 (1.5×10⁻³, 1.5e-3), 千位分隔符 (1,000), 分数 (1/2), 前导零 (.5)
NUM = r"(?:(?:\d{1,3}(?:,\d{3})*(?:\.\d+)?)|(?:\d+(?:\.\d+)?)|(?:\.\d+))"  # Support 1,000.5 format
NUM_SCIENTIFIC = rf"(?:{NUM}\s*[×x]\s*10\s*[⁻⁻-]?\s*\d+|{NUM}\s*[eE][+-]?\d+)"  # 1.5×10⁻³ or 1.5e-3
NUM_ANY = rf"(?:{NUM_SCIENTIFIC}|{NUM})"  # Any numeric format
RANGE_NUM = rf"({NUM_ANY})\s*[-–—~±]\s*({NUM_ANY})"  # Range: 5-7, 5–7, 5~7, 5±0.5

# Enhanced pH patterns: e.g., "pH 7.4", "at pH=5.5", "pH range 6-8", "acidic pH", "pH (7.4)"
PH_PATTERNS = [
    # Basic patterns with various separators
    re.compile(rf"\bpH\s*[=:~≈±]?\s*({NUM_ANY})", re.IGNORECASE),
    re.compile(rf"\bpH\s*\({NUM_ANY}\)", re.IGNORECASE),  # pH (7.4)
    re.compile(rf"\bpH\s*of\s*({NUM_ANY})", re.IGNORECASE),
    # Range patterns
    re.compile(rf"\bpH\s*(?:range|values?)\s*(?:of\s*)?{RANGE_NUM}", re.IGNORECASE),
    re.compile(rf"\bpH\s*(?:between|from)\s*{RANGE_NUM}", re.IGNORECASE),
    re.compile(rf"\bpH\s*{RANGE_NUM}", re.IGNORECASE),  # pH 5-7
    # Contextual patterns
    re.compile(rf"\bat\s*pH\s*[=:]?\s*({NUM_ANY})", re.IGNORECASE),
    re.compile(rf"\bpH\s*({NUM_ANY})\s*buffer", re.IGNORECASE),
    re.compile(rf"\b(?:in|with|using)\s*(?:a\s*)?pH\s*(?:of\s*)?({NUM_ANY})", re.IGNORECASE),
    re.compile(rf"\b(?:at|to)\s*pH\s*({NUM_ANY})", re.IGNORECASE),
    # Adjustment patterns
    re.compile(rf"\bpH\s*(?:was|is|was\s*set)?\s*(?:adjusted?\s*(?:to)?|maintained\s*at|kept\s*at)\s*({NUM_ANY})", re.IGNORECASE),
    re.compile(rf"\bpH\s*(?:maintained|kept|set)\s*(?:at|to)\s*({NUM_ANY})", re.IGNORECASE),
    # Qualitative pH with optional numeric
    re.compile(rf"\b(?:under|at)\s*(?:an?\s*)?(?:acidic|basic|alkaline|neutral)\s*(?:pH\s*)?(?:of\s*)?({NUM_ANY})?", re.IGNORECASE),
    re.compile(rf"\b(?:acidic|basic|alkaline|neutral)\s*(?:pH\s*)?(?:of\s*|at\s*)?({NUM_ANY})?", re.IGNORECASE),
    # Implicit pH expressions (value near "pH" keyword)
    re.compile(rf"\b({NUM_ANY})\s*(?:pH|pH\s*value)", re.IGNORECASE),  # 7.4 pH
    re.compile(rf"~{NUM_ANY}\s*(?:pH|and\s*pH)", re.IGNORECASE),  # ~7.4 pH
]

# Enhanced temperature patterns: "25 C", "25°C", "298 K", "room temperature", "4°C", "-20°C"
TEMP_PATTERNS = [
    # Basic temperature with units (Celsius)
    re.compile(rf"(-?{NUM_ANY})\s*°?\s*C(?:elsius)?\b", re.IGNORECASE),  # Support negative: -20°C
    re.compile(rf"(-?{NUM_ANY})\s*deg(?:rees?)?\s*(?:C|celsius|centigrade)", re.IGNORECASE),
    re.compile(rf"\b(?:at\s*)?(-?{NUM_ANY})\s*°C", re.IGNORECASE),
    # Kelvin (convert to Celsius)
    re.compile(rf"({NUM_ANY})\s*K(?:elvin)?\b", re.IGNORECASE),
    # Fahrenheit (convert to Celsius: (°F - 32) × 5/9)
    re.compile(rf"({NUM_ANY})\s*°?\s*F(?:ahrenheit)?\b", re.IGNORECASE),
    # Range patterns
    re.compile(rf"temperature\s*(?:of\s*)?{RANGE_NUM}\s*°?C", re.IGNORECASE),
    re.compile(rf"\bfrom\s*({NUM_ANY})\s*to\s*({NUM_ANY})\s*°?C", re.IGNORECASE),
    re.compile(rf"\bbetween\s*({NUM_ANY})\s*and\s*({NUM_ANY})\s*°?C", re.IGNORECASE),
    re.compile(rf"\b({NUM_ANY})\s*[-–]\s*({NUM_ANY})\s*°C", re.IGNORECASE),  # 20-25°C
    # Contextual patterns
    re.compile(rf"\b(?:heated|cooled|incubated|stored|maintained)\s*(?:at|to|for)\s*({NUM_ANY})\s*°?C", re.IGNORECASE),
    re.compile(rf"\b({NUM_ANY})\s*°C\s*(?:for|during|over|at)", re.IGNORECASE),
    re.compile(rf"\btemperature\s*(?:was|is)?\s*(?:set|maintained|kept|adjusted)\s*(?:at|to)\s*({NUM_ANY})\s*°?C", re.IGNORECASE),
    re.compile(rf"\b(?:in|with|using|under)\s*(?:a\s*)?temperature\s*(?:of\s*)?({NUM_ANY})\s*°?C", re.IGNORECASE),
    # Special temperature expressions
    re.compile(rf"\broom\s*temperature\s*(?:\(~?({NUM_ANY})\s*°C\))?", re.IGNORECASE),  # ~25°C
    re.compile(rf"\bRT\s*(?:\(~?({NUM_ANY})\s*°C\))?", re.IGNORECASE),  # RT (~25°C)
    re.compile(rf"\b(?:cold|ice|frozen|refrigerat)\s*(?:temperature|conditions?)\s*(?:\(~?({NUM_ANY})\s*°C\))?", re.IGNORECASE),  # ~4°C
    re.compile(rf"\b(?:body|physiological|physio)\s*temperature\s*(?:\(~?({NUM_ANY})\s*°C\))?", re.IGNORECASE),  # ~37°C
    re.compile(rf"\bambient\s*temperature", re.IGNORECASE),  # Ambient (~25°C)
    # Implicit temperature (number + context words)
    re.compile(rf"({NUM_ANY})\s*(?:°C|C|K)\s*(?:incubation|storage|treatment|experiment)", re.IGNORECASE),
]

# Enhanced concentration patterns: more units and formats, support scientific notation
CONC_PATTERNS = [
    # Mass/volume units (mg/mL, µg/mL, etc.)
    re.compile(rf"({NUM_ANY})\s*(mg\s*[/·×]\s*mL|mg/mL|mg\s*mL\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(µg\s*[/·×]\s*mL|ug\s*[/·×]\s*mL|mcg\s*[/·×]\s*mL|µg/mL|ug/mL|μg/mL)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(ng\s*[/·×]\s*mL|ng/mL)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(pg\s*[/·×]\s*mL|pg/mL)\b", re.IGNORECASE),
    # Percentage concentrations
    re.compile(rf"({NUM_ANY})\s*%\s*(?:w/v|wt/vol|weight/volume|w/w|wt/wt|v/v)?\b", re.IGNORECASE),
    # Molarity units
    re.compile(rf"({NUM_ANY})\s*(mM|mm|millimolar|milli[- ]molar|millimol\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(µM|uM|μM|micromolar|micro[- ]molar|micromol\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(nM|nanomolar|nano[- ]molar|nanomol\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(pM|picomolar|pico[- ]molar|picomol\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(fM|femtomolar|femto[- ]molar)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(M|molar)\b(?!\w)", re.IGNORECASE),  # Avoid matching "Molecular", "Methods"
    # Volume/volume units
    re.compile(rf"({NUM_ANY})\s*(g\s*[/·×]\s*L|g/L|g\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(mg\s*[/·×]\s*L|mg/L|mg\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(g\s*[/·×]\s*dL|g/dL)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(mol\s*[/·×]\s*L|mol/L|mol\s*L\s*[-−⁻]?\s*1)\b", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(mmol\s*[/·×]\s*L|mmol/L)\b", re.IGNORECASE),
    # Activity units
    re.compile(rf"({NUM_ANY})\s*(units?\s*[/·×]\s*mL|U\s*[/·×]\s*mL|U/mL|IU\s*[/·×]\s*mL|IU/mL)\b", re.IGNORECASE),
    # Contextual concentration patterns
    re.compile(rf"concentration\s*(?:of\s*)?{RANGE_NUM}\s*(mg/mL|µg/mL|μg/mL|ug/mL|mM|μM|µM|uM)", re.IGNORECASE),
    re.compile(rf"\b(?:at|with|using)\s*(?:a\s*)?concentration\s*(?:of\s*)?({NUM_ANY})\s*(mg/mL|µg/mL|μg/mL|ug/mL|mM|μM|µM|uM)", re.IGNORECASE),
    re.compile(rf"\bconcentration\s*(?:was|is)?\s*(?:adjusted?\s*(?:to)?|set\s*to|maintained\s*at)\s*({NUM_ANY})\s*(mg/mL|µg/mL|μg/mL|ug/mL|mM|μM|µM|uM)", re.IGNORECASE),
    re.compile(rf"\b(?:protein|sample|solution)\s*(?:at|of|was)\s*({NUM_ANY})\s*(mg/mL|µg/mL|μg/mL|ug/mL|mM|μM|µM|uM)", re.IGNORECASE),
    # Dilution/fold patterns
    re.compile(rf"\b({NUM_ANY})\s*x\s*(?:concentrated?|fold)", re.IGNORECASE),
    re.compile(rf"\bdiluted?\s*(?:to\s*|at\s*)?({NUM_ANY})\s*(?:x|fold|mg/mL|µg/mL|μg/mL|ug/mL|mM|μM|µM|uM)", re.IGNORECASE),
    # Scientific notation (1.5×10⁻³ M)
    re.compile(rf"({NUM_SCIENTIFIC})\s*(M|mM|µM|μM|uM|nM|pM|mg/mL|µg/mL|μg/mL|ug/mL)\b", re.IGNORECASE),
]

# Enhanced stability outcome cues with more comprehensive patterns
OUTCOME_CUES = [
    # Stability terms
    re.compile(r"\b(stable|stability|unstable|instability)\b", re.IGNORECASE),
    re.compile(r"\b(stabiliz\w*|destabiliz\w*)\b", re.IGNORECASE),
    re.compile(r"\b(maintain\w*\s*stability|retain\w*\s*stability)\b", re.IGNORECASE),
    re.compile(r"\b(thermal\s*stability|thermostable)\b", re.IGNORECASE),
    re.compile(r"\b(long[- ]?term\s*stability|storage\s*stability)\b", re.IGNORECASE),
    
    # Denaturation and unfolding
    re.compile(r"\b(denatur\w*|unfold\w*|refold\w*)\b", re.IGNORECASE),
    re.compile(r"\b(native\s*structure|native\s*state|native\s*conformation)\b", re.IGNORECASE),
    
    # Aggregation and precipitation
    re.compile(r"\b(aggregat\w*|precipitat\w*|clump\w*)\b", re.IGNORECASE),
    re.compile(r"\b(fibril\w*|amyloid\w*)\b", re.IGNORECASE),
    re.compile(r"\b(gel\w*|gelation)\b", re.IGNORECASE),
    
    # Solubility terms
    re.compile(r"\b(solubility|soluble|insoluble|solubiliz\w*|solubilis\w*)\b", re.IGNORECASE),
    re.compile(r"\b(dissolv\w*|dissolution)\b", re.IGNORECASE),
    
    # Activity and function
    re.compile(r"\b(activity|active|inactive|bioactivity)\b", re.IGNORECASE),
    re.compile(r"\b(functional|function\w*|dysfunction\w*)\b", re.IGNORECASE),
    re.compile(r"\b(enzymatic\s*activity|catalytic\s*activity)\b", re.IGNORECASE),
    
    # Degradation
    re.compile(r"\b(degradat\w*|degrad\w*)\b", re.IGNORECASE),
    re.compile(r"\b(hydroly\w*|oxidat\w*|proteoly\w*)\b", re.IGNORECASE),
]

# Negation patterns for context analysis
NEGATION_PATTERNS = [
    re.compile(r"\b(not|no|never|without|lack\w*|absent|fail\w*)\b", re.IGNORECASE),
    re.compile(r"\b(un|in|dis|de)(?=\w)", re.IGNORECASE),  # Prefixes
    re.compile(r"\b(prevent\w*|avoid\w*|inhibit\w*|suppress\w*)\b", re.IGNORECASE),
    re.compile(r"\b(loss\s*of|decrease\w*\s*in|reduction\s*in)\b", re.IGNORECASE),
]

# Comparison patterns for relative stability
COMPARISON_PATTERNS = [
    re.compile(r"\b(more|less|higher|lower|greater|smaller)\s*(?:\w+\s*)*(?:stable|stability)", re.IGNORECASE),
    re.compile(r"\b(increase\w*|decrease\w*|improve\w*|enhance\w*|reduce\w*)\s*(?:\w+\s*)*(?:stability)", re.IGNORECASE),
    re.compile(r"\b(compared\s*to|relative\s*to|versus|vs\.?|than)\b", re.IGNORECASE),
    re.compile(r"\b(fold\s*(?:increase|decrease)|times\s*(?:more|less))\b", re.IGNORECASE),
]

# Enhanced Ionic strength patterns - Extended
IONIC_STRENGTH_PATTERNS = [
    # Direct ionic strength mentions
    re.compile(rf"ionic\s*strength\s*(?:of|was|at|=\s*|:)?\s*({NUM_ANY})\s*(M|mM|µM|μM|uM)?", re.IGNORECASE),
    re.compile(rf"I\s*=\s*({NUM_ANY})\s*(M|mM|µM|μM|uM)", re.IGNORECASE),  # I = 0.15 M
    re.compile(rf"µ\s*=\s*({NUM_ANY})\s*(M|mM|µM|μM|uM)", re.IGNORECASE),  # μ = 0.15 M
    re.compile(rf"μ\s*=\s*({NUM_ANY})\s*(M|mM|µM|μM|uM)", re.IGNORECASE),  # μ = 0.15 M (alternative μ)
    # Salt-based ionic strength inference (NaCl, KCl are 1:1 salts, I ≈ concentration)
    re.compile(rf"({NUM_ANY})\s*(M|mM|µM|μM|uM)\s*(?:NaCl|KCl|sodium\s*chloride|potassium\s*chloride)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(mM|μM|µM|uM|M)\s*(?:Tris|HEPES|phosphate|buffer|PBS|TBS|MOPS|PIPES|MES)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(mM|μM|µM|uM|M)\s*(?:MgCl2|CaCl2|ZnCl2|MnCl2|NiCl2|CuCl2|FeCl3)", re.IGNORECASE),
    # Buffer ionic strength
    re.compile(rf"({NUM_ANY})\s*(mM|M)\s*buffer\s*(?:with|at)\s*(?:ionic\s*strength|I\s*=)", re.IGNORECASE),
    re.compile(rf"buffer\s*(?:at|with|of)\s*({NUM_ANY})\s*(mM|M)\s*(?:ionic\s*strength|I)", re.IGNORECASE),
]

# Enhanced Additive patterns - Extended
ADDITIVE_PATTERNS = [
    # Stabilizers and osmolytes (with concentration)
    re.compile(rf"({NUM_ANY})\s*(mM|M|%|w/v|wt/vol)\s*(glycerol|sucrose|trehalose|mannitol|sorbitol|xylitol|glucose|fructose)", re.IGNORECASE),
    re.compile(rf"(?:with|in|containing|added|supplemented\s*with)\s*({NUM_ANY})\s*(?:%|mM|M)?\s*(glycerol|sucrose|trehalose|mannitol|sorbitol|xylitol)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(?:%|mM|M)\s*(?:of\s*)?(glycerol|sucrose|trehalose|mannitol)", re.IGNORECASE),
    # Reducing agents
    re.compile(rf"({NUM_ANY})\s*(mM|μM|µM|uM)\s*(DTT|TCEP|BME|β-mercaptoethanol|mercaptoethanol|2-mercaptoethanol)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(mM|μM|µM|uM)\s*(GSH|glutathione|reduced\s*glutathione|dithiothreitol)", re.IGNORECASE),
    re.compile(rf"(?:with|in|added)\s*({NUM_ANY})\s*(mM|μM)?\s*(DTT|TCEP|BME|mercaptoethanol)", re.IGNORECASE),
    # Chelators
    re.compile(rf"({NUM_ANY})\s*(mM|μM|µM|uM)\s*(EDTA|EGTA|citrate|citric\s*acid)", re.IGNORECASE),
    re.compile(rf"(?:with|in)\s*({NUM_ANY})\s*(mM)?\s*(EDTA|EGTA)", re.IGNORECASE),
    # Polymers
    re.compile(rf"({NUM_ANY})\s*(kDa|Da|%|w/v)\s*PEG\s*({NUM_ANY})?", re.IGNORECASE),
    re.compile(rf"PEG\s*({NUM_ANY})\s*(kDa|Da|MW)\s*(?:at|with|of)?\s*({NUM_ANY})?", re.IGNORECASE),
    re.compile(rf"PEG\s*(?:{NUM_ANY})\s*(?:kDa)?\s*(?:at|of)?\s*({NUM_ANY})\s*(?:%|mg/mL)", re.IGNORECASE),
    # Surfactants and detergents
    re.compile(rf"({NUM_ANY})\s*(%|mM|M)\s*(Tween\s*\d+|Triton\s*X[- ]?\d+|SDS|CTAB|CHAPS|NP-40)", re.IGNORECASE),
    re.compile(rf"(?:surfactant|detergent)\s*(?:concentration)?\s*(?:of|at)?\s*({NUM_ANY})\s*(%|mM)?", re.IGNORECASE),
    # Generic additive mentions (may not have concentration)
    re.compile(rf"(?:stabilizer|stabilizing\s*agent|protectant|cryoprotectant|preservative|excipient)", re.IGNORECASE),
    # Specific additives by name (with optional concentration)
    re.compile(rf"(?:NaCl|KCl|sodium\s*chloride|potassium\s*chloride)\s*(?:at|of|=\s*)?({NUM_ANY})?\s*(mM|M)?", re.IGNORECASE),
    re.compile(rf"(?:BSA|albumin|bovine\s*serum\s*albumin|serum)\s*(?:at|of|=\s*)?({NUM_ANY})?\s*(?:mg/mL|%)?", re.IGNORECASE),  # BSA as additive
    re.compile(rf"(?:Tween|Triton|SDS|CHAPS|DTT|EDTA|glycerol|sucrose|trehalose)\s*(?:at|of|=\s*)?({NUM_ANY})?\s*(?:%|mM|M)?", re.IGNORECASE),  # Catch common additives
]

# Time patterns - Incubation/storage time
TIME_PATTERNS = [
    # Minutes
    re.compile(rf"({NUM_ANY})\s*(?:min|minutes|minute)\b", re.IGNORECASE),
    re.compile(rf"for\s*({NUM_ANY})\s*(?:min|minutes)", re.IGNORECASE),
    re.compile(rf"(?:incubated?|stored?|kept|maintained)\s*(?:for|at|in)\s*({NUM_ANY})\s*(?:min|minutes)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(?:min|minutes)\s*(?:at|of|for)", re.IGNORECASE),
    # Hours
    re.compile(rf"({NUM_ANY})\s*(?:h|hr|hours|hour)\b", re.IGNORECASE),
    re.compile(rf"for\s*({NUM_ANY})\s*(?:h|hours)", re.IGNORECASE),
    re.compile(rf"(?:incubated?|stored?|kept|maintained)\s*(?:for|at|in)\s*({NUM_ANY})\s*(?:h|hours)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(?:h|hours)\s*(?:at|of|for)", re.IGNORECASE),
    # Days
    re.compile(rf"({NUM_ANY})\s*(?:d|days|day)\b", re.IGNORECASE),
    re.compile(rf"stored?\s*(?:for|at|in)\s*({NUM_ANY})\s*(?:days|day)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(?:days|day)\s*(?:at|of|for)", re.IGNORECASE),
    # Time range
    re.compile(rf"({NUM_ANY})\s*[-–—~±]\s*({NUM_ANY})\s*(?:min|minutes|h|hours|d|days)", re.IGNORECASE),
    re.compile(rf"from\s*({NUM_ANY})\s*to\s*({NUM_ANY})\s*(?:min|minutes|h|hours)", re.IGNORECASE),
    # Common time expressions
    re.compile(rf"(?:overnight|ON|o\.n\.)", re.IGNORECASE),  # Overnight (~12-16 hours)
    re.compile(rf"(?:24|48|72|96)\s*(?:h|hours|hr)", re.IGNORECASE),  # 24h, 48h, 72h
    re.compile(rf"(\d+)\s*weeks?", re.IGNORECASE),  # Weeks (convert to days)
]

# Shear rate patterns (1/s or s⁻¹)
SHEAR_RATE_PATTERNS = [
    re.compile(rf"shear\s*rate\s*(?:of|was|at|=\s*|:)?\s*({NUM_ANY})\s*(?:1/s|s⁻¹|s\^-1|per\s*second|sec⁻¹)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(?:1/s|s⁻¹|s\^-1|sec⁻¹)\s*(?:shear|stirring|mixing|rate)", re.IGNORECASE),
    re.compile(rf"shear\s*(?:rate|stress)\s*(?:of|at|=\s*)?({NUM_ANY})\s*(?:Pa|1/s|s⁻¹)", re.IGNORECASE),
    re.compile(rf"stirred?\s*(?:at|with|for)\s*({NUM_ANY})\s*(?:rpm|RPM|1/s|s⁻¹)", re.IGNORECASE),
    re.compile(rf"agitated?\s*(?:at|with)\s*({NUM_ANY})\s*(?:rpm|RPM|1/s|s⁻¹)", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*(?:rpm|RPM)\s*(?:stirring|agitation|mixing|shear)", re.IGNORECASE),
    # Viscosity-related shear
    re.compile(rf"viscosity\s*(?:at|of|with)\s*({NUM_ANY})\s*(?:1/s|s⁻¹|shear|shear\s*rate)", re.IGNORECASE),
    re.compile(rf"rotational\s*(?:speed|velocity|rate)\s*(?:of|at)?\s*({NUM_ANY})\s*(?:rpm|1/s|s⁻¹)", re.IGNORECASE),
]

# Pressure patterns (bar, atm, MPa, psi, kPa)
PRESSURE_PATTERNS = [
    # Bar
    re.compile(rf"({NUM_ANY})\s*bar\b", re.IGNORECASE),
    re.compile(rf"pressure\s*(?:of|at|was|is|=\s*|:)?\s*({NUM_ANY})\s*bar", re.IGNORECASE),
    # Atmosphere
    re.compile(rf"({NUM_ANY})\s*atm\b", re.IGNORECASE),
    re.compile(rf"pressure\s*(?:of|at|was|is|=\s*|:)?\s*({NUM_ANY})\s*atm", re.IGNORECASE),
    # MPa and kPa
    re.compile(rf"({NUM_ANY})\s*MPa\b", re.IGNORECASE),
    re.compile(rf"pressure\s*(?:of|at|was|is|=\s*|:)?\s*({NUM_ANY})\s*MPa", re.IGNORECASE),
    re.compile(rf"({NUM_ANY})\s*kPa\b", re.IGNORECASE),
    re.compile(rf"pressure\s*(?:of|at|was|is|=\s*|:)?\s*({NUM_ANY})\s*kPa", re.IGNORECASE),
    # PSI (less common in biology, but included)
    re.compile(rf"({NUM_ANY})\s*psi\b", re.IGNORECASE),
    re.compile(rf"pressure\s*(?:of|at|was|is|=\s*|:)?\s*({NUM_ANY})\s*psi", re.IGNORECASE),
    # High pressure processing terms
    re.compile(rf"high\s*pressure\s*(?:of|at|=\s*)?\s*({NUM_ANY})?\s*(?:bar|MPa|atm)?", re.IGNORECASE),
    re.compile(rf"HPP\s*(?:at|of|=\s*)?\s*({NUM_ANY})?\s*(?:bar|MPa|atm)?", re.IGNORECASE),  # High Pressure Processing
    # Atmospheric pressure reference
    re.compile(rf"(?:atmospheric|ambient)\s*pressure", re.IGNORECASE),
    # Pascal (Pa)
    re.compile(rf"({NUM_ANY})\s*Pa\b(?!\w)", re.IGNORECASE),  # Avoid matching "Paper", "Parameter"
    re.compile(rf"pressure\s*(?:of|at|was|is|=\s*)?\s*({NUM_ANY})\s*Pa\b", re.IGNORECASE),
]

# Section/context patterns for weighting
SECTION_PATTERNS = {
    'methods': re.compile(r"\b(methods?|materials?\s*and\s*methods?|experimental\s*(?:section|procedure))\b", re.IGNORECASE),
    'results': re.compile(r"\b(results?|findings?|observations?)\b", re.IGNORECASE),
    'discussion': re.compile(r"\b(discussion|conclusion\w*)\b", re.IGNORECASE),
    'introduction': re.compile(r"\b(introduction|background)\b", re.IGNORECASE),
    'abstract': re.compile(r"\b(abstract|summary)\b", re.IGNORECASE),
}