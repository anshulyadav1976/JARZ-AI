"""Investment analysis functionality."""
from typing import Optional
from ..scansan_client import get_scansan_client
from ..a2ui_builder import build_text_component, build_surface_update, build_data_model_update, build_begin_rendering
from .tools import InvestmentAnalysisResult, execute_get_rent_forecast


async def execute_get_investment_analysis(
    location: str,
    property_value: Optional[float] = None,
    deposit_percent: float = 25,
    mortgage_rate: float = 4.5,
    mortgage_years: int = 25,
) -> InvestmentAnalysisResult:
    """
    Execute comprehensive investment analysis.
    
    Fetches market data, calculates rental yield, ROI, cash flow, and other metrics.
    
    Args:
        location: Location string (postcode or area name)
        property_value: Purchase price (if not provided, uses market average)
        deposit_percent: Deposit percentage (default 25%)
        mortgage_rate: Annual mortgage rate (default 4.5%)
        mortgage_years: Mortgage term in years (default 25)
        
    Returns:
        InvestmentAnalysisResult with comprehensive metrics
    """
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
        
        # 3. Calculate investment metrics
        # Deposit and mortgage
        deposit_amount = property_value * (deposit_percent / 100)
        mortgage_amount = property_value - deposit_amount
        
        # Monthly mortgage payment (using standard mortgage formula)
        monthly_rate = (mortgage_rate / 100) / 12
        num_payments = mortgage_years * 12
        if monthly_rate > 0:
            monthly_mortgage = mortgage_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_mortgage = mortgage_amount / num_payments
        
        # Operating costs (maintenance, insurance, management, void periods, etc.)
        # Typically 20-30% of rent
        monthly_operating_costs = predicted_rent_pcm * 0.25
        
        # Total monthly costs
        monthly_costs = monthly_mortgage + monthly_operating_costs
        
        # Monthly cash flow
        monthly_cash_flow = predicted_rent_pcm - monthly_costs
        
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
        
        # 4. Build A2UI messages for display with visual cards
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
                {"label": "Monthly Mortgage", "value": f"-£{monthly_mortgage:,.0f}"},
                {"label": "Operating Costs (25%)", "value": f"-£{monthly_operating_costs:,.0f}"},
                {"label": "Net Cash Flow", "value": f"{'£' if monthly_cash_flow >= 0 else '-£'}{abs(monthly_cash_flow):,.0f}", "highlight": True},
            ],
            variant="success" if monthly_cash_flow >= 0 else "destructive"
        ))
        
        # Card 4: Annual Summary
        components.append(build_card_component(
            card_id="annual_summary_card",
            title="Annual Summary",
            items=[
                {"label": "Annual Rent Income", "value": f"£{annual_rent:,.0f}"},
                {"label": "Annual Costs", "value": f"£{annual_costs:,.0f}"},
                {"label": "Annual Cash Flow", "value": f"{'£' if annual_cash_flow >= 0 else '-£'}{abs(annual_cash_flow):,.0f}"},
                {"label": "Total Initial Investment", "value": f"£{total_investment:,.0f}"},
            ],
            variant="default"
        ))
        
        # Surface update
        a2ui_messages.append(build_surface_update(components))
        
        # Data model for investment calculator
        a2ui_messages.append(build_data_model_update([
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
        ], path="/investment"))
        
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
            a2ui_messages=[],
            summary=f"Error analyzing investment for {location}: {str(e)}",
        )
