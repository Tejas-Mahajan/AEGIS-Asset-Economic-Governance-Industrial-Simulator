# Project Plan — Smart Industrial Asset Evaluation System

## Module Overview & Merge Order
1. **Data Simulation (`data_simulation/`)**: NASA C-MAPSS FD001 dataset replay simulator, noise/missing/anomaly injection, and Event Injection API.
2. **Predictive Analytics (`predictive_analytics/`)**: RUL prediction model with confidence bands derived from sensor historical data.
3. **Economic Governance (`economic_governance/`)**: Analytic Hierarchy Process (AHP) asset ranking, CVaR loss distribution calculation, budget allocation, and reactive vs predictive savings comparator.
4. **Dashboard & Integration (`dashboard/`)**: Interactive Streamlit dashboard visualizing health, rankings, risk/budget allocations, and event injection ripples.

## Guidelines & Constraints
- Build each module incrementally against mocks first.
- Maintain character-for-character field alignment with `SCHEMAS.md`.
- Ensure end-to-end integration and visual ripple demonstration across all views upon event injection.
