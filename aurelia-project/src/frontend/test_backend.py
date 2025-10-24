# from flask import Flask, jsonify, request

# app = Flask(__name__)

# @app.route('/query', methods=['POST'])
# def query():
#     data = request.json
#     concept = data.get("concept", "Unknown")
#     return jsonify({
#         "concept": concept,
#         "source": "test",
#         "note": {
#             "Definition": f"This is a test definition for {concept}",
#             "Formula": "Test formula here",
#             "Example": "Example calculation",
#             "Use Case": "Common applications in finance"
#         }
#     })

# @app.route('/seed', methods=['POST'])
# def seed():
#     data = request.json
#     concept = data.get("concept", "Unknown")
#     return jsonify({
#         "source": "cached", 
#         "concept": concept,
#         "message": f"Concept '{concept}' seeded successfully"
#     })

# @app.route('/list', methods=['GET'])
# def list_concepts():
#     return jsonify([
#         {
#             "concept": "Sharpe Ratio",
#             "source": "cached",
#             "note": {
#                 "Definition": "Risk-adjusted return measure",
#                 "Formula": "(Return - Risk-free rate) / Standard deviation",
#                 "Example": "If portfolio returns 12% with 15% volatility and risk-free rate is 2%, Sharpe = (12-2)/15 = 0.67",
#                 "Use Case": "Comparing portfolio performance"
#             }
#         },
#         {
#             "concept": "Beta",
#             "source": "cached",
#             "note": {
#                 "Definition": "Measure of systematic risk relative to market",
#                 "Formula": "Covariance(asset, market) / Variance(market)",
#                 "Example": "Beta of 1.5 means 50% more volatile than market",
#                 "Use Case": "Asset pricing and risk assessment"
#             }
#         },
#         {
#             "concept": "Alpha",
#             "source": "cached",
#             "note": {
#                 "Definition": "Excess return over expected return given beta",
#                 "Formula": "Actual Return - [Risk-free rate + Beta × (Market return - Risk-free rate)]",
#                 "Example": "Positive alpha indicates outperformance",
#                 "Use Case": "Evaluating fund manager performance"
#             }
#         }
#     ])

# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify({"status": "healthy", "service": "AURELIA Test Backend"})

# if __name__ == '__main__':
#     print("=" * 60)
#     print("AURELIA Test Backend API")
#     print("=" * 60)
#     print("Running on: http://localhost:8000")
#     print("")
#     print("Available endpoints:")
#     print("  POST /query  - Generate concept note")
#     print("  POST /seed   - Seed concept to cache")
#     print("  GET  /list   - List all cached concepts")
#     print("  GET  /health - Health check")
#     print("=" * 60)
#     app.run(port=8000, debug=True)



####################################### version 2 claude
from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data with PDF references
SAMPLE_CONCEPTS = {
    "sharpe ratio": {
        "concept": "Sharpe Ratio",
        "source": "financial_toolbox",
        "references": [
            {
                "document": "Portfolio_Risk_Management.pdf",
                "section": "Risk-Adjusted Performance Metrics",
                "page": 47,
                "chunk_id": "chunk_0234",
                "score": 0.9234
            },
            {
                "document": "Quantitative_Finance_Fundamentals.pdf",
                "section": "Performance Measurement",
                "page": 112,
                "chunk_id": "chunk_0891",
                "score": 0.8756
            }
        ],
        "note": {
            "Definition": "The Sharpe Ratio is a measure of risk-adjusted return that calculates the excess return per unit of risk (standard deviation). It was developed by Nobel laureate William F. Sharpe.",
            "Formula": "Sharpe Ratio = (Rp - Rf) / σp, where Rp is portfolio return, Rf is risk-free rate, and σp is portfolio standard deviation",
            "Example": "If a portfolio returns 12% with 15% volatility and the risk-free rate is 2%, the Sharpe Ratio = (12% - 2%) / 15% = 0.67",
            "Use Case": "Used to compare portfolio performance accounting for risk. Higher Sharpe ratios indicate better risk-adjusted returns. Values above 1 are considered good, above 2 are very good, and above 3 are excellent.",
            "Interpretation": "A Sharpe ratio of 0.67 means the portfolio generates 0.67 units of excess return for each unit of risk taken."
        }
    },
    "beta": {
        "concept": "Beta",
        "source": "cached",
        "references": [
            {
                "document": "Asset_Pricing_Theory.pdf",
                "section": "Systematic Risk Measurement",
                "page": 23,
                "chunk_id": "chunk_0145",
                "score": 0.9456
            }
        ],
        "note": {
            "Definition": "Beta measures an asset's systematic risk relative to the overall market. It quantifies how much an asset's returns move in relation to market returns.",
            "Formula": "β = Covariance(Ri, Rm) / Variance(Rm), where Ri is asset return and Rm is market return",
            "Example": "A stock with beta of 1.5 is expected to move 50% more than the market. If market rises 10%, stock should rise 15%.",
            "Use Case": "Beta is central to the Capital Asset Pricing Model (CAPM) and used for portfolio construction, hedging, and risk assessment."
        }
    },
    "black-scholes model": {
        "concept": "Black-Scholes Model",
        "source": "wikipedia",
        "note": {
            "Definition": "The Black-Scholes model is a mathematical model for pricing European-style options, developed by Fischer Black, Myron Scholes, and Robert Merton in 1973.",
            "Formula": "C = S₀N(d₁) - Ke^(-rT)N(d₂), where d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)",
            "Example": "For a stock at $100, strike $105, 1 year to expiry, 20% volatility, 5% interest rate, the call option value can be calculated using the formula.",
            "Use Case": "Widely used for pricing options, calculating implied volatility, and managing option portfolios. Foundation for modern derivatives pricing.",
            "Limitations": "Assumes constant volatility, no dividends, European exercise only, and log-normal price distribution."
        }
    }
}

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    concept = data.get("concept", "").lower().strip()
    
    # Check if concept exists in sample data
    if concept in SAMPLE_CONCEPTS:
        return jsonify(SAMPLE_CONCEPTS[concept])
    
    # Otherwise return a generic response with Wikipedia source
    return jsonify({
        "concept": data.get("concept", "Unknown"),
        "source": "wikipedia",
        "note": {
            "Definition": f"This is a Wikipedia fallback definition for {data.get('concept', 'Unknown')}",
            "Formula": "Formula not available from corpus",
            "Example": "Example calculation would appear here",
            "Use Case": "Common applications in finance",
            "Note": "This content was retrieved from Wikipedia as it was not found in the Financial Toolbox corpus."
        }
    })

@app.route('/seed', methods=['POST'])
def seed():
    data = request.json
    concept = data.get("concept", "").lower().strip()
    
    # Simulate seeding - return appropriate source
    if concept in SAMPLE_CONCEPTS:
        source = SAMPLE_CONCEPTS[concept]["source"]
    else:
        source = "wikipedia"
    
    return jsonify({
        "source": source, 
        "concept": data.get("concept", "Unknown"),
        "message": f"Concept '{data.get('concept')}' seeded successfully"
    })

@app.route('/list', methods=['GET'])
def list_concepts():
    # Return all sample concepts
    return jsonify(list(SAMPLE_CONCEPTS.values()) + [
        {
            "concept": "Alpha",
            "source": "financial_toolbox",
            "references": [
                {
                    "document": "Active_Portfolio_Management.pdf",
                    "section": "Performance Attribution",
                    "page": 89,
                    "chunk_id": "chunk_0456",
                    "score": 0.9123
                }
            ],
            "note": {
                "Definition": "Alpha represents the excess return of an investment relative to the return predicted by a pricing model like CAPM.",
                "Formula": "α = Ri - [Rf + βi(Rm - Rf)]",
                "Example": "If a fund returns 15% when CAPM predicts 12%, alpha is +3%",
                "Use Case": "Evaluating fund manager skill and identifying sources of outperformance"
            }
        },
        {
            "concept": "Modern Portfolio Theory",
            "source": "wikipedia",
            "note": {
                "Definition": "Modern Portfolio Theory (MPT) is a framework for constructing portfolios that maximize expected return for a given level of risk.",
                "Key Concepts": "Developed by Harry Markowitz in 1952. Uses diversification to optimize portfolio risk-return profiles.",
                "Example": "Combining uncorrelated assets can reduce overall portfolio risk without sacrificing returns.",
                "Use Case": "Foundation for asset allocation and portfolio construction in investment management."
            }
        },
        {
            "concept": "Duration",
            "source": "rag",
            "references": [
                {
                    "document": "Fixed_Income_Securities.pdf",
                    "section": "Bond Price Sensitivity",
                    "page": 156,
                    "chunk_id": "chunk_1234",
                    "score": 0.9567
                },
                {
                    "document": "Interest_Rate_Risk_Management.pdf",
                    "section": "Duration Measures",
                    "page": 78,
                    "chunk_id": "chunk_0567",
                    "score": 0.8934
                }
            ],
            "note": {
                "Definition": "Duration measures the weighted average time to receive a bond's cash flows. It indicates price sensitivity to interest rate changes.",
                "Formula": "Modified Duration = Macaulay Duration / (1 + YTM/n)",
                "Example": "A bond with duration of 5 years will decrease approximately 5% in price for a 1% increase in yields.",
                "Use Case": "Used for immunization strategies, hedging interest rate risk, and portfolio management.",
                "Types": "Macaulay Duration (time-weighted), Modified Duration (price sensitivity), Effective Duration (accounts for embedded options)"
            }
        }
    ])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "AURELIA Test Backend"})

if __name__ == '__main__':
    print("=" * 60)
    print("AURELIA Test Backend API")
    print("=" * 60)
    print("Running on: http://localhost:8000")
    print("")
    print("Available endpoints:")
    print("  POST /query  - Generate concept note")
    print("  POST /seed   - Seed concept to cache")
    print("  GET  /list   - List all cached concepts")
    print("  GET  /health - Health check")
    print("=" * 60)
    app.run(port=8000, debug=True)