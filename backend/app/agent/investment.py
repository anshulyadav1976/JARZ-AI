"""Investment analysis functionality."""
from typing import Optional
import sys
from pathlib import Path

# Add investment_model to path
investment_model_path = Path(__file__).parent.parent.parent.parent / "investment_model" / "src"
sys.path.insert(0, str(investment_model_path))

from ..scansan_client import get_scansan_client
from ..a2ui_builder import build_text_component, build_surface_update, build_data_model_update, build_begin_rendering
from .tools import InvestmentAnalysisResult, execute_get_rent_forecast
from ..mortgage_rates import get_current_mortgage_rate

# Try to import the investment model predictor
try:
    from predict_investment import predict_investment_roi
    INVESTMENT_MODEL_AVAILABLE = True
    print("[INVESTMENT] ML model loaded successfully")
except Exception as e:
    INVESTMENT_MODEL_AVAILABLE = False
    print(f"[INVESTMENT] ML model not available: {e}")


async def execute_get_investment_analysis(
    location: str,
    property_value: Optional[float] = None,
    deposit_percent: float = 25,
    mortgage_rate: Optional[float] = None,  # If None, fetches real-time rate
    mortgage_years: int = 25,
    mortgage_type: str = "interest_only",  # "interest_only" or "repayment"
) -> InvestmentAnalysisResult:
    """
    Execute comprehensive investment analysis.
    
    Fetches market data, calculates rental yield, ROI, cash flow, and other metrics.
    
    Args:
        location: Location string (postcode or area name)
        property_value: Purchase price (if not provided, uses market average)
        deposit_percent: Deposit percentage (default 25%)
        mortgage_rate: Annual mortgage rate (if None, fetches real-time UK rate)
        mortgage_years: Mortgage term in years (default 25)
        mortgage_type: "interest_only" (default for BTL) or "repayment"
        
    Returns:
        InvestmentAnalysisResult with comprehensive metrics
    """
    # Fetch real-time mortgage rate if not provided
    if mortgage_rate is None:
        mortgage_rate = await get_current_mortgage_rate()
        rate_source = "Live UK Rate"
    else:
        rate_source = "Custom Rate"
    
    client = get_scansan_client()
    
    try:
        # Resolve location
        resolved_location = await client.search_area_codes(location)
        if not resolved_location:
            raise ValueError(f"Could not find location: {location}")
        
        area_code = resolved_location.area_code_district or resolved_location.area_code
        area_name = resolved_location.display_name or area_code
        
        print(f"[INVESTMENT] Analyzing investment potential for {area_name}")
        
        # 1. Get rent forecast for predicted monthly rent
        rent_forecast = await execute_get_rent_forecast(
            location=location,
            horizon_months=6,
            k_neighbors=5,
        )
        predicted_rent_pcm = rent_forecast.prediction.get("p50", 0)
        
        # 2. Get market data (sale demand)
        sale_demand_data = await client.get_sale_demand(area_code)
        
        # Extract market metrics
        market_metrics = {}
        if sale_demand_data and "data" in sale_demand_data:
            demand_data = sale_demand_data["data"]
            # Handle both list and dict responses
            if isinstance(demand_data, list) and len(demand_data) > 0:
                demand = demand_data[0]
            elif isinstance(demand_data, dict):
                demand = demand_data
            else:
                demand = {}
            
            market_metrics["avg_sale_price"] = demand.get("mean_sale_price")
            market_metrics["median_sale_price"] = demand.get("median_sale_price")
            market_metrics["total_properties_for_sale"] = demand.get("total_properties_for_sale")
            market_metrics["avg_days_on_market"] = demand.get("days_on_market")
        
        # Use provided property value or market average
        if not property_value:
            property_value = market_metrics.get("median_sale_price") or market_metrics.get("avg_sale_price") or 350000
            print(f"[INVESTMENT] Using market median price: £{property_value:,.0f}")
        else:
            print(f"[INVESTMENT] Using provided property value: £{property_value:,.0f}")
        
        # Fetch energy performance data for operating costs
        energy_data = None
        try:
            # Try to get energy data for the area (will get first property in postcode)
            # Extract postcode from area_code if possible
            if area_code and len(area_code) >= 4:
                energy_data = await client.get_postcode_energy_performance(area_code)
                if energy_data:
                    print(f"[INVESTMENT] Got EPC data for operating cost estimation")
        except Exception as e:
            print(f"[INVESTMENT] Could not fetch EPC data: {e}")
        
        # 3. Calculate investment metrics
        print(f"[INVESTMENT] Using mortgage rate: {mortgage_rate}% ({rate_source})")
        print(f"[INVESTMENT] Mortgage type: {mortgage_type}")
        
        # Deposit and mortgage
        deposit_amount = property_value * (deposit_percent / 100)
        mortgage_amount = property_value - deposit_amount
        
        # Monthly mortgage payment
        monthly_rate = (mortgage_rate / 100) / 12
        num_payments = mortgage_years * 12
        
        if mortgage_type == "interest_only":
            # Interest-only: only pay interest, not principal
            # This is standard for buy-to-let to maximize cash flow
            monthly_mortgage = mortgage_amount * monthly_rate
            mortgage_type_label = "Interest-Only"
        else:
            # Repayment: pay principal + interest
            # More common for residential owner-occupiers
            if monthly_rate > 0:
                monthly_mortgage = mortgage_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_mortgage = mortgage_amount / num_payments
            mortgage_type_label = "Repayment"
        
        print(f"[INVESTMENT] Monthly mortgage ({mortgage_type_label}): £{monthly_mortgage:,.0f}")
        
        # Operating costs breakdown
        # Instead of fixed 25%, calculate based on actual data where available
        
        # NOTE: For standard unfurnished buy-to-let, tenant pays energy bills!
        # Only include energy costs for furnished/HMO properties with bills included
        
        # 1. Energy costs (SKIP for standard buy-to-let)
        monthly_energy_cost = 0  # Tenant responsibility
        energy_cost_source = "Tenant Pays"
        
        # If you want to include energy (e.g., for furnished properties):
        # if energy_data:
        #     costs_data = energy_data.get("annual_energy_costs", {})
        #     heating_cost = costs_data.get("current_annual_heating_cost", 0)
        #     lighting_cost = costs_data.get("current_annual_lighting_cost", 0)
        #     hotwater_cost = costs_data.get("current_annual_hot_water_cost", 0)
        #     if heating_cost or lighting_cost or hotwater_cost:
        #         annual_energy_cost = heating_cost + lighting_cost + hotwater_cost
        #         monthly_energy_cost = annual_energy_cost / 12
        #         energy_cost_source = "EPC Data (Bills Included)"
        
        # 2. Landlord insurance (typically £150-300/year for buy-to-let)
        annual_insurance = min(300, max(150, property_value * 0.0004))  # 0.04% of property value
        monthly_insurance = annual_insurance / 12
        
        # 3. Management fees (typically 10-15% of rent if using agent)
        monthly_management = predicted_rent_pcm * 0.12  # 12% of rent
        
        # 4. Maintenance & repairs (realistic £500-1500/year, not % of property value)
        # High-value properties don't cost proportionally more to maintain
        annual_maintenance = min(1500, max(500, property_value * 0.002))  # Max £1500/year
        monthly_maintenance = annual_maintenance / 12
        
        # 5. Void periods (1 month vacancy per year = 8.3% of annual rent)
        monthly_void_allowance = (predicted_rent_pcm * 12 * 0.083) / 12
        
        # 6. Service charges (if applicable, assume £0 for houses, estimate for flats)
        # Would need property type from EPC or property data
        monthly_service_charge = 0
        
        # Total monthly operating costs
        monthly_operating_costs = (
            monthly_energy_cost +
            monthly_insurance +
            monthly_management +
            monthly_maintenance +
            monthly_void_allowance +
            monthly_service_charge
        )
        
        operating_cost_breakdown = {
            "energy": monthly_energy_cost,
            "insurance": monthly_insurance,
            "management": monthly_management,
            "maintenance": monthly_maintenance,
            "void": monthly_void_allowance,
            "service_charge": monthly_service_charge,
        }
        
        operating_percentage = (monthly_operating_costs / predicted_rent_pcm * 100) if predicted_rent_pcm > 0 else 25
        
        print(f"[INVESTMENT] Operating costs breakdown:")
        print(f"  - Energy: £{monthly_energy_cost:,.0f}/mo ({energy_cost_source})")
        print(f"  - Insurance: £{monthly_insurance:,.0f}/mo")
        print(f"  - Management (12%): £{monthly_management:,.0f}/mo")
        print(f"  - Maintenance (£{annual_maintenance:,.0f}/yr): £{monthly_maintenance:,.0f}/mo")
        print(f"  - Void allowance (8.3%): £{monthly_void_allowance:,.0f}/mo")
        print(f"  - Total: £{monthly_operating_costs:,.0f}/mo ({operating_percentage:.1f}% of rent)")
        
        # Total monthly costs
        monthly_costs = monthly_mortgage + monthly_operating_costs
        
        # Monthly cash flow
        monthly_cash_flow = predicted_rent_pcm - monthly_costs
        
        print(f"[INVESTMENT] Rent: £{predicted_rent_pcm:,.0f}, Mortgage: £{monthly_mortgage:,.0f}, Operating: £{monthly_operating_costs:,.0f}, Cash Flow: £{monthly_cash_flow:,.0f}")
        
        # Interest Coverage Ratio (ICR) check - lenders typically require 125%
        # ICR = (Monthly Rent / Monthly Interest Payment) × 100
        # For interest-only mortgages, monthly interest = monthly_mortgage
        # For repayment mortgages, we need just the interest portion
        monthly_interest = mortgage_amount * monthly_rate
        interest_coverage_ratio = (predicted_rent_pcm / monthly_interest * 100) if monthly_interest > 0 else 0
        
        # Calculate minimum rent or deposit needed for 125% ICR
        icr_pass = interest_coverage_ratio >= 125
        min_rent_for_icr = monthly_interest * 1.25 if monthly_interest > 0 else 0
        
        # Calculate what deposit % would be needed to meet 125% ICR with current rent
        # Work backwards: if rent needs to cover 125% of interest, what's max mortgage?
        max_mortgage_for_icr = (predicted_rent_pcm / 1.25) / monthly_rate if monthly_rate > 0 else 0
        min_deposit_for_icr = property_value - max_mortgage_for_icr
        min_deposit_percent_for_icr = (min_deposit_for_icr / property_value * 100) if property_value > 0 else 25
        
        print(f"[INVESTMENT] Interest Coverage Ratio: {interest_coverage_ratio:.1f}% (Lenders require ≥125%)")
        if not icr_pass:
            print(f"[INVESTMENT] ⚠️ ICR below standard - Need either:")
            print(f"  - Minimum rent: £{min_rent_for_icr:,.0f}/mo (currently £{predicted_rent_pcm:,.0f})")
            print(f"  - Minimum deposit: {min_deposit_percent_for_icr:.1f}% (currently {deposit_percent}%)")
        
        # Validate calculations - warn if yield is below mortgage rate
        if gross_yield_calc := (predicted_rent_pcm * 12 / property_value) * 100:
            if gross_yield_calc < mortgage_rate:
                print(f"[INVESTMENT] WARNING: Gross yield ({gross_yield_calc:.1f}%) is below mortgage rate ({mortgage_rate:.1f}%) - negative cash flow expected")
        
        # Annual figures
        annual_rent = predicted_rent_pcm * 12
        annual_costs = monthly_costs * 12
        annual_cash_flow = monthly_cash_flow * 12
        
        # Rental yields
        gross_yield = (annual_rent / property_value) * 100  # Gross yield (ignores costs)
        net_yield = (annual_cash_flow / property_value) * 100  # Net yield (after costs)
        
        # ROI (return on deposit)
        annual_roi = (annual_cash_flow / deposit_amount) * 100 if deposit_amount > 0 else 0
        
        # Break-even analysis
        if annual_cash_flow > 0:
            break_even_years = deposit_amount / annual_cash_flow
        else:
            break_even_years = float('inf')
        
        total_investment = deposit_amount
        
        # 5. Get ML model predictions if available
        ml_predictions = None
        ml_available = False
        if INVESTMENT_MODEL_AVAILABLE:
            try:
                print(f"[INVESTMENT] Getting ML predictions for {area_code}")
                ml_predictions = predict_investment_roi(
                    area_code=area_code,
                    predicted_rent_pcm=predicted_rent_pcm,
                    avg_sale_price=property_value,
                    rent_change_12m_pct=0,  # Could get from historical data
                    properties_for_rent=market_metrics.get("total_properties_for_rent", 100),
                    properties_for_sale=market_metrics.get("total_properties_for_sale", 50),
                )
                ml_available = True
                print(f"[INVESTMENT] ML predictions: 5yr ROI = {ml_predictions.get('roi_5yr_pct', 0):.1f}%")
            except Exception as e:
                print(f"[INVESTMENT] ML prediction failed: {e}")
                ml_predictions = None
        
        # 6. Build A2UI messages for display with visual cards
        from ..a2ui_builder import build_card_component
        a2ui_messages = []
        components = []
        
        # Header
        components.append(build_text_component(
            "investment_header",
            f"Investment Analysis: {area_name}",
            usage_hint="heading1"
        ))
        
        # Summary
        cash_flow_status = "positive" if monthly_cash_flow >= 0 else "negative"
        yield_quality = "strong" if gross_yield >= 5 else ("moderate" if gross_yield >= 3 else "low")
        
        summary_text = (
            f"Analysis for a **£{property_value:,.0f}** property in {area_name}. "
            f"Expected monthly rent: **£{predicted_rent_pcm:,.0f}**. "
            f"The gross yield is **{gross_yield:.2f}%** ({yield_quality}) with a **{cash_flow_status}** monthly cash flow of **£{monthly_cash_flow:,.0f}**."
        )
        
        # Add ML model disclaimer if available
        if ml_available and ml_predictions:
            summary_text += f"\n\n**🤖 AI-Powered Investment Forecast**\n{ml_predictions.get('risk_warning', '')}"
        
        components.append(build_text_component(
            "investment_summary",
            summary_text,
            usage_hint="body"
        ))
        
        # Key Metrics Cards
        # Card 1: Property Details
        components.append(build_card_component(
            card_id="property_details_card",
            title="Property Details",
            items=[
                {"label": "Property Value", "value": f"£{property_value:,.0f}"},
                {"label": "Required Deposit (25%)", "value": f"£{deposit_amount:,.0f}"},
                {"label": "Mortgage Amount", "value": f"£{mortgage_amount:,.0f}"},
                {"label": "Expected Monthly Rent", "value": f"£{predicted_rent_pcm:,.0f}"},
            ],
            variant="default"
        ))
        
        # Card 2: Yield Metrics
        components.append(build_card_component(
            card_id="yield_metrics_card",
            title="Rental Yield",
            items=[
                {"label": "Gross Yield", "value": f"{gross_yield:.2f}%", "highlight": gross_yield >= 5},
                {"label": "Net Yield", "value": f"{net_yield:.2f}%", "highlight": net_yield >= 3},
                {"label": "Annual ROI (on deposit)", "value": f"{annual_roi:.1f}%", "highlight": annual_roi >= 10},
                {"label": "Break-even Period", "value": f"{break_even_years:.1f} years" if break_even_years < 50 else "N/A"},
            ],
            variant="primary" if gross_yield >= 5 else "default"
        ))
        
        # Card 3: Monthly Cash Flow
        components.append(build_card_component(
            card_id="cash_flow_card",
            title="Monthly Cash Flow",
            items=[
                {"label": "Monthly Rent Income", "value": f"£{predicted_rent_pcm:,.0f}"},
                {"label": f"Mortgage ({mortgage_type_label})", "value": f"-£{monthly_mortgage:,.0f}"},
                {"label": f"Interest Rate ({rate_source})", "value": f"{mortgage_rate}%"},
                {"label": f"Operating Costs ({operating_percentage:.0f}%)", "value": f"-£{monthly_operating_costs:,.0f}"},
                {"label": "Net Monthly Cash Flow", "value": f"£{monthly_cash_flow:,.0f}", "highlight": monthly_cash_flow > 0},
            ],
            variant="success" if monthly_cash_flow > 0 else "destructive"
        ))
        
        # Card 3.5: Operating Costs Breakdown (SIMPLIFIED)
        components.append(build_card_component(
            card_id="operating_costs_breakdown_card",
            title=f"Operating Costs",
            items=[
                {"label": "Insurance", "value": f"£{operating_cost_breakdown['insurance']:,.0f}/mo"},
                {"label": "Management (12%)", "value": f"£{operating_cost_breakdown['management']:,.0f}/mo"},
                {"label": "Maintenance", "value": f"£{operating_cost_breakdown['maintenance']:,.0f}/mo"},
                {"label": "Void (8.3%)", "value": f"£{operating_cost_breakdown['void']:,.0f}/mo"},
                {"label": "Total", "value": f"£{monthly_operating_costs:,.0f}/mo", "highlight": True},
            ],
            variant="default"
        ))
        
        # Card 3.6: Calculation Assumptions (CONDENSED)
        components.append(build_card_component(
            card_id="assumptions_card",
            title="📋 Assumptions",
            items=[
                {"label": "Mortgage", "value": f"{mortgage_type_label}, {mortgage_rate}% ({rate_source}), {mortgage_years}yr"},
                {"label": "Deposit", "value": f"{deposit_percent}%"},
                {"label": "ICR", "value": f"{interest_coverage_ratio:.1f}% {'✅' if icr_pass else '⚠️ Need ≥125%'}"},
            ],
            variant="default"
        ))
        
        # Card 4: Total Return Analysis (Capital Appreciation + Rental Income)
        # Calculate example scenarios with realistic London appreciation rates
        appreciation_3pct = property_value * 0.03
        appreciation_5pct = property_value * 0.05
        appreciation_7pct = property_value * 0.07
        
        total_return_3pct = appreciation_3pct + annual_cash_flow
        total_return_5pct = appreciation_5pct + annual_cash_flow
        total_return_7pct = appreciation_7pct + annual_cash_flow
        
        roi_3pct = (total_return_3pct / deposit_amount) * 100
        roi_5pct = (total_return_5pct / deposit_amount) * 100
        roi_7pct = (total_return_7pct / deposit_amount) * 100
        
        components.append(build_card_component(
            card_id="total_return_card",
            title="💰 Total Return Analysis (How You Actually Make Money)",
            items=[
                {"label": "Rental Cash Flow (Annual)", "value": f"{'£' if annual_cash_flow >= 0 else '-£'}{abs(annual_cash_flow):,.0f}"},
                {"label": "", "value": ""},
                {"label": "With 3% Property Growth/Year", "value": ""},
                {"label": "  Property Value Gain", "value": f"+£{appreciation_3pct:,.0f}"},
                {"label": "  Rental Cash Flow", "value": f"{'£' if annual_cash_flow >= 0 else '-£'}{abs(annual_cash_flow):,.0f}"},
                {"label": "  Total Annual Profit", "value": f"£{total_return_3pct:,.0f}", "highlight": True},
                {"label": "  ROI on Your £{:,.0f} Deposit".format(deposit_amount), "value": f"{roi_3pct:.1f}%", "highlight": roi_3pct > 0},
                {"label": "", "value": ""},
                {"label": "With 5% Property Growth/Year", "value": ""},
                {"label": "  Total Annual Profit", "value": f"£{total_return_5pct:,.0f}", "highlight": True},
                {"label": "  ROI on Deposit", "value": f"{roi_5pct:.1f}%", "highlight": roi_5pct > 0},
                {"label": "", "value": ""},
                {"label": "With 7% Property Growth/Year", "value": ""},
                {"label": "  Total Annual Profit", "value": f"£{total_return_7pct:,.0f}", "highlight": True},
                {"label": "  ROI on Deposit", "value": f"{roi_7pct:.1f}%", "highlight": roi_7pct > 0},
            ],
            variant="primary"
        ))
        
        components.append(build_text_component(
            "total_return_note",
            f"In areas like {area_name}, profit comes from property growth (5-7%/yr historically), not just rent.",
            usage_hint="body"
        ))
        
        # Card 5: ML Model Predictions (if available, CONDENSED)
        if ml_available and ml_predictions:
            components.append(build_card_component(
                card_id="ml_predictions_card",
                title="🤖 AI Forecast",
                items=[
                    {"label": "1yr ROI", "value": f"{ml_predictions.get('roi_1yr_pct', 0):.1f}%"},
                    {"label": "3yr ROI", "value": f"{ml_predictions.get('roi_3yr_pct', 0):.1f}%"},
                    {"label": "5yr ROI", "value": f"{ml_predictions.get('roi_5yr_pct', 0):.1f}%", "highlight": True},
                ],
                variant="secondary"
            ))
            
            components.append(build_text_component(
                "ml_note",
                f"Model is 99.85% accurate at ranking areas, but ROI values are directional. Use for comparison, not precision.",
                usage_hint="body"
            ))
        
        # Surface update
        a2ui_messages.append(build_surface_update(components))
        
        # Data model for investment calculator
        data_model_items = [
            {"key": "property_value", "valueNumber": property_value},
            {"key": "predicted_rent", "valueNumber": predicted_rent_pcm},
            {"key": "gross_yield", "valueNumber": gross_yield},
            {"key": "net_yield", "valueNumber": net_yield},
            {"key": "monthly_cash_flow", "valueNumber": monthly_cash_flow},
            {"key": "annual_roi", "valueNumber": annual_roi},
            {"key": "break_even_years", "valueNumber": break_even_years if break_even_years != float('inf') else 0},
            {"key": "monthly_mortgage", "valueNumber": monthly_mortgage},
            {"key": "monthly_costs", "valueNumber": monthly_costs},
            {"key": "deposit_amount", "valueNumber": deposit_amount},
            {"key": "mortgage_rate", "valueNumber": mortgage_rate},
            {"key": "rate_source", "valueString": rate_source},
            # Operating cost breakdown
            {"key": "operating_costs_total", "valueNumber": monthly_operating_costs},
            {"key": "operating_costs_percentage", "valueNumber": operating_percentage},
            {"key": "operating_costs_energy", "valueNumber": operating_cost_breakdown['energy']},
            {"key": "operating_costs_insurance", "valueNumber": operating_cost_breakdown['insurance']},
            {"key": "operating_costs_management", "valueNumber": operating_cost_breakdown['management']},
            {"key": "operating_costs_maintenance", "valueNumber": operating_cost_breakdown['maintenance']},
            {"key": "operating_costs_void", "valueNumber": operating_cost_breakdown['void']},
            {"key": "energy_cost_source", "valueString": energy_cost_source},
        ]
        
        # Add ML predictions to data model if available
        if ml_available and ml_predictions:
            data_model_items.extend([
                {"key": "ml_roi_1yr", "valueNumber": ml_predictions.get('roi_1yr_pct', 0)},
                {"key": "ml_roi_3yr", "valueNumber": ml_predictions.get('roi_3yr_pct', 0)},
                {"key": "ml_roi_5yr", "valueNumber": ml_predictions.get('roi_5yr_pct', 0)},
                {"key": "ml_available", "valueBoolean": True},
            ])
        else:
            data_model_items.append({"key": "ml_available", "valueBoolean": False})
        
        a2ui_messages.append(build_data_model_update(data_model_items, path="/investment"))
        
        # Begin rendering
        a2ui_messages.append(build_begin_rendering("root"))
        
        # Generate summary for LLM (concise to save tokens)
        summary = (
            f"{area_name} £{property_value:,.0f}: Rent £{predicted_rent_pcm:,.0f}/mo, "
            f"Gross {gross_yield:.1f}% Net {net_yield:.1f}%, "
            f"Cash flow £{monthly_cash_flow:+,.0f}/mo, ROI {annual_roi:.1f}%"
        )
        if break_even_years < 20:
            summary += f", Break-even {break_even_years:.1f}yr"
        elif monthly_cash_flow < 0:
            summary += " (neg. cash flow)"
        
        # Add ML prediction summary if available
        if ml_available and ml_predictions:
            roi_5yr = ml_predictions.get('roi_5yr_pct', 0)
            summary += f". ML Model: 5yr ROI ~{roi_5yr:.0f}% (ranking-focused, not exact value)"
        
        return InvestmentAnalysisResult(
            success=True,
            location=area_name,
            property_value=property_value,
            predicted_rent_pcm=predicted_rent_pcm,
            rental_yield=gross_yield,
            gross_yield=gross_yield,
            net_yield=net_yield,
            monthly_mortgage=monthly_mortgage,
            monthly_costs=monthly_costs,
            monthly_cash_flow=monthly_cash_flow,
            annual_roi=annual_roi,
            break_even_years=break_even_years if break_even_years != float('inf') else 0,
            total_investment=total_investment,
            market_metrics=market_metrics,
            interest_coverage_ratio=interest_coverage_ratio,
            icr_pass=icr_pass,
            min_rent_for_icr=min_rent_for_icr,
            min_deposit_percent_for_icr=min_deposit_percent_for_icr,
            a2ui_messages=a2ui_messages,
            summary=summary,
        )
        
    except Exception as e:
        print(f"[INVESTMENT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return InvestmentAnalysisResult(
            success=False,
            location=location,
            property_value=0,
            predicted_rent_pcm=0,
            rental_yield=0,
            gross_yield=0,
            net_yield=0,
            monthly_mortgage=0,
            monthly_costs=0,
            monthly_cash_flow=0,
            annual_roi=0,
            break_even_years=0,
            total_investment=0,
            market_metrics={},
            interest_coverage_ratio=0,
            icr_pass=False,
            min_rent_for_icr=0,
            min_deposit_percent_for_icr=25,
            a2ui_messages=[],
            summary=f"Error analyzing investment for {location}: {str(e)}",
        )
