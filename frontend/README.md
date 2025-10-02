# Frontend Module - DoE-Assist

## Responsibilities
- User Query Interface
- Manual Data Input Interface
- Parameter Recommendation Display and Visualization
- Experimental Result Feedback Interface

## Tech Stack
- React.js 18+
- TypeScript
- Material-UI / Ant Design
- D3.js (Data Visualization)
- Axios (API Calls)

## Project Structure
```
frontend/
├── src/
│   ├── components/     # Reusable Components
│   ├── pages/         # Page Components
│   ├── services/      # API Services
│   ├── utils/         # Utility Functions
│   ├── types/         # TypeScript Type Definitions
│   └── styles/        # Style Files
├── public/            # Static Assets
└── package.json       # Dependency Configuration
```

## Main Pages
1. **Homepage**: Project Introduction and Quick Query
2. **Parameter Query**: Input experiment type, get parameter recommendations
3. **Data Input**: Manual experimental data input
4. **Results Display**: Visualize prediction results
5. **Feedback Submission**: Submit experimental result feedback

## Development Commands
```bash
npm install          # Install dependencies
npm start           # Start development server
npm run build       # Build production version
npm test            # Run tests
```

## Design Principles
- Responsive design, mobile support
- Intuitive user interface
- Real-time data updates
- Good error handling
