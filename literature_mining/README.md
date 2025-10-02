# Literature Mining Engine - DoE-Assist

## Responsibilities
- Automatically mine experimental parameters from scientific literature
- Extract data from online databases
- NLP text processing and entity recognition
- Data cleaning and structuring

## Tech Stack
- Python 3.9+
- BeautifulSoup4
- requests
- NLTK, spaCy
- Transformers

## Data Sources
- Semantic Scholar API
- CrossRef API
- PubMed
- Academic journal websites

## Project Structure
```
literature_mining/
├── scrapers/         # Web Scrapers
├── nlp/             # NLP Processing
├── extractors/      # Data Extractors
├── parsers/         # Data Parsers
└── storage/         # Data Storage
```

## Main Functions
1. **Literature Search**: Search relevant literature based on keywords
2. **Content Extraction**: Extract experimental parameters and results
3. **Entity Recognition**: Identify chemical substances, experimental conditions, etc.
4. **Data Validation**: Validate the accuracy of extracted data
5. **Data Storage**: Store data in database

## Supported Data Types
- Solubility experimental data
- Crystallization experimental data
- Reaction condition data
- Material property data

## Usage Example
```python
from literature_mining.extractors import SolubilityExtractor

extractor = SolubilityExtractor()
data = extractor.extract_from_paper(paper_url)
```
