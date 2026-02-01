# Embodied Carbon Calculation

## Overview

This document describes the embodied carbon calculation methodology implemented in JARZ-AI's Sustainability Assessment feature. The calculation follows industry standards for Life Cycle Assessment (LCA) of buildings and provides audit-grade, planning-compliant results.

## Standards & Compliance

The implementation is compliant with:

- **EN 15978:2011** - Sustainability of construction works - Assessment of environmental performance of buildings - Calculation method
- **EN 15804** - Environmental Product Declarations (EPD) methodology
- **ISO 14040/14044** - Environmental management - Life cycle assessment - Principles and framework
- **RICS Whole Life Carbon Assessment** (2nd Edition, 2023)
- **ICE Database v3.0** - Inventory of Carbon & Energy (University of Bath)

## Scope: Product & Construction Stages (A1-A5)

The calculation covers the following lifecycle stages per EN 15978:

### A1-A3: Product Stage (Cradle-to-Gate)
- **A1**: Raw material extraction and processing
- **A2**: Transport to manufacturing facility
- **A3**: Manufacturing of construction products

These stages are bundled in Environmental Product Declarations (EPDs) and represent the embodied carbon of materials as delivered to site.

### A4: Transport to Site
Transport of materials and products from manufacturing gate to construction site.

### A5: Construction/Installation Process
On-site construction activities including equipment use, waste processing, and energy consumption during construction.

## Methodology

### Step 1: Material Quantity Estimation (Bill of Quantities)

Material quantities are estimated based on property type and Gross Internal Area (GIA). Intensity factors represent typical UK residential construction:

#### Material Intensity Factors by Property Type

| Material | Flat | Terraced | Semi-Det. | Detached | Bungalow |
|----------|------|----------|-----------|----------|----------|
| **Concrete** (m³/m²) | 0.25 | 0.30 | 0.35 | 0.50 | 0.28 |
| **Rebar** (kg/m²) | 15 | 18 | 20 | 30 | 16 |
| **Structural Steel** (kg/m²) | 5 | 8 | 10 | 15 | 6 |
| **Brick** (units/m²) | 40 | 50 | 55 | 70 | 45 |
| **Timber** (m³/m²) | 0.03 | 0.04 | 0.045 | 0.06 | 0.035 |

**Formula:**
```
Material Quantity = Property GIA (m²) × Material Intensity Factor
```

### Step 2: Emission Factor Application (A1-A3)

Emission factors from ICE Database v3.0:

| Material | Emission Factor | Unit | Source |
|----------|----------------|------|--------|
| **Concrete** | 280 | kg CO₂e/m³ | ICE v3.0 (average UK mix) |
| **Rebar** | 1.20 | kg CO₂e/kg | ICE v3.0 (recycled steel) |
| **Structural Steel** | 1.70 | kg CO₂e/kg | ICE v3.0 (primary steel) |
| **Brick** | 0.22 | kg CO₂e/unit | ICE v3.0 (common brick) |
| **Timber** | 110 | kg CO₂e/m³ | ICE v3.0 (sawn softwood) |

**Formula:**
```
A1-A3 Embodied Carbon (kg CO₂e) = Σ (Material Quantity × Emission Factor)
```

**Important:** Emission factors from EPDs already include mining, smelting, and manufacturing processes. Do NOT calculate these separately.

### Step 3: Transport Calculation (A4)

**Assumptions:**
- Average transport distance: **120 km** (typical UK supply chain)
- Transport emission factor: **0.1 kg CO₂e/t·km** (road freight, DEFRA conversion factors)

**Formula:**
```
Total Material Mass (tonnes) = Σ (Material Quantity × Material Density)

A4 Transport (kg CO₂e) = Total Mass (tonnes) × Distance (km) × 0.1 kg CO₂e/t·km
```

**Material Densities:**
- Concrete: 2,400 kg/m³
- Rebar: 7,850 kg/m³ (steel density)
- Structural Steel: 7,850 kg/m³
- Brick: 2.5 kg/unit (standard UK brick)
- Timber: 500 kg/m³ (softwood)

### Step 4: Construction Process (A5)

Per RICS Whole Life Carbon Assessment guidelines, construction process emissions are estimated as:

**Formula:**
```
A5 Construction (kg CO₂e) = A1-A3 Total × 0.05
```

This 5% factor covers:
- On-site equipment operation (diesel generators, excavators, cranes)
- Temporary works (scaffolding, formwork)
- Waste processing and disposal
- Site energy consumption

### Step 5: Normalization & Reporting

#### Total Embodied Carbon
```
Total Embodied Carbon (kg CO₂e) = A1-A3 + A4 + A5
```

#### Intensity per m²
```
Embodied Carbon Intensity (kg CO₂e/m²) = Total Embodied Carbon / Property GIA
```

#### Annualized Value
Using a **60-year reference study period** (standard for UK residential buildings):

```
Annual Embodied Carbon (tonnes CO₂e/year) = Total Embodied Carbon (kg) / 1000 / 60
```

## Example Calculation

### Property Details
- **Type:** Semi-Detached House
- **Gross Internal Area (GIA):** 120 m²

### Step 1: Material Quantities
- Concrete: 120 m² × 0.35 m³/m² = **42 m³**
- Rebar: 120 m² × 20 kg/m² = **2,400 kg**
- Structural Steel: 120 m² × 10 kg/m² = **1,200 kg**
- Brick: 120 m² × 55 units/m² = **6,600 units**
- Timber: 120 m² × 0.045 m³/m² = **5.4 m³**

### Step 2: A1-A3 Emissions
- Concrete: 42 m³ × 280 kg CO₂e/m³ = **11,760 kg CO₂e**
- Rebar: 2,400 kg × 1.20 kg CO₂e/kg = **2,880 kg CO₂e**
- Structural Steel: 1,200 kg × 1.70 kg CO₂e/kg = **2,040 kg CO₂e**
- Brick: 6,600 units × 0.22 kg CO₂e/unit = **1,452 kg CO₂e**
- Timber: 5.4 m³ × 110 kg CO₂e/m³ = **594 kg CO₂e**

**A1-A3 Total:** 11,760 + 2,880 + 2,040 + 1,452 + 594 = **18,726 kg CO₂e**

### Step 3: A4 Transport
- Concrete: 42 m³ × 2,400 kg/m³ = 100,800 kg = 100.8 tonnes
- Rebar: 2,400 kg × 1 = 2.4 tonnes
- Steel: 1,200 kg × 1 = 1.2 tonnes
- Brick: 6,600 units × 2.5 kg = 16,500 kg = 16.5 tonnes
- Timber: 5.4 m³ × 500 kg/m³ = 2,700 kg = 2.7 tonnes

**Total Mass:** 100.8 + 2.4 + 1.2 + 16.5 + 2.7 = **123.6 tonnes**

**A4 Transport:** 123.6 tonnes × 120 km × 0.1 kg CO₂e/t·km = **1,483 kg CO₂e**

### Step 4: A5 Construction
**A5 Construction:** 18,726 kg × 0.05 = **936 kg CO₂e**

### Step 5: Results
- **Total Embodied Carbon:** 18,726 + 1,483 + 936 = **21,145 kg CO₂e** = **21.1 tonnes CO₂e**
- **Embodied Carbon Intensity:** 21,145 kg / 120 m² = **176 kg CO₂e/m²**
- **Annualized Embodied Carbon:** 21.1 tonnes / 60 years = **0.35 tonnes CO₂e/year**

## Integration with Operational Carbon

The Sustainability Assessment combines embodied carbon with operational carbon to provide a comprehensive view:

```
Total Annual Carbon Footprint = Operational Emissions + Annualized Embodied Carbon
```

Where:
- **Operational Emissions:** Annual CO₂ emissions from energy use (heating, lighting, appliances)
- **Annualized Embodied Carbon:** Total embodied carbon divided by 60-year lifespan

## Assumptions & Limitations

### Assumptions
1. **Material intensities** are based on typical UK residential construction practices
2. **Transport distance** assumes average UK supply chain (120 km)
3. **Construction process** emissions use RICS default (5% of A1-A3)
4. **Reference study period** is 60 years per UK standards
5. **No BIM data** available; quantities estimated from property type and size

### Limitations
1. **Property-specific design** is not considered (e.g., basement, extensions, heritage features)
2. **Regional variations** in construction practices not accounted for
3. **Stages B-D** (use, maintenance, end-of-life) are not calculated (operational carbon covers use stage energy only)
4. **Sequestration** benefits of timber not included (conservative approach)
5. **Uncertainty range** not quantified (±15-20% typical for bill-of-quantities estimation)

### Appropriate Use Cases
✅ **Suitable for:**
- Planning applications (comparative assessment)
- ESG reporting (annual disclosure)
- Investment decision support (portfolio comparison)
- Tenant engagement (carbon awareness)

❌ **Not suitable for:**
- Detailed design optimization (requires BIM-based LCA)
- Carbon offsetting certification (requires site-specific data)
- Contractor procurement (requires accurate BoQ)

## Data Sources & References

1. **EN 15978:2011** - Sustainability of construction works - Assessment of environmental performance of buildings - Calculation method
2. **EN 15804:2012+A2:2019** - Sustainability of construction works - Environmental product declarations - Core rules
3. **ISO 14040:2006** - Environmental management - Life cycle assessment - Principles and framework
4. **ISO 14044:2006** - Environmental management - Life cycle assessment - Requirements and guidelines
5. **RICS Whole Life Carbon Assessment for the Built Environment** (2nd Edition, 2023)
6. **ICE Database v3.0** - Inventory of Carbon & Energy, Circular Ecology/University of Bath (2019)
7. **UK Government GHG Conversion Factors** - DEFRA (2024)

## Implementation Details

### Backend
- **File:** `backend/app/agent/tools.py`
- **Function:** `execute_calculate_carbon()`
- **Data Source:** ScanSan API (property details: type, size, location)
- **Calculation:** ~150 lines of EN 15978-compliant Python code

### Frontend Display
- **File:** `frontend/components/CarbonCard.tsx`
- **Component:** `CarbonCard`
- **Features:**
  - EN 15978 badge (standards compliance indicator)
  - Total embodied carbon (tonnes CO₂e)
  - Embodied carbon intensity (kg CO₂e/m²)
  - Stage breakdown (A1-A3, A4, A5)
  - Annualized value (60-year lifespan)
  - Total annual carbon footprint (operational + embodied)

### A2UI Integration
- **File:** `backend/app/a2ui_builder.py`
- **Function:** `build_carbon_card()`
- **Data Bindings:** 6 embodied carbon parameters streamed to frontend

## Audit Trail & Transparency

The calculation includes comprehensive logging at each stage:
- Material quantities calculated
- A1-A3 emissions per material
- Total material mass
- A4 transport calculation
- A5 construction calculation
- Normalization and annualization

All calculations are traceable and reproducible for audit purposes.

## Future Enhancements

Potential improvements for future versions:
1. **BIM Integration:** Direct quantity take-off from BIM models
2. **Regional Factors:** Location-based transport distances and construction practices
3. **Material-Specific EPDs:** Manufacturer-specific emission factors
4. **Stages B-D:** Maintenance, replacement, deconstruction, and end-of-life
5. **Sequestration:** Biogenic carbon storage in timber
6. **Uncertainty Analysis:** Monte Carlo simulation for confidence intervals
7. **Benchmarking:** Comparison against UK housing stock averages
8. **Circular Economy:** Secondary material content and reuse potential

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Author:** JARZ-AI Team  
**Compliance:** EN 15978:2011, RICS WLC 2023, ICE Database v3.0
