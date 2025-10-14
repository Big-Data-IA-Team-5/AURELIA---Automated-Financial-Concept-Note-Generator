from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    concept = data.get("concept", "Unknown")
    return jsonify({
        "concept": concept,
        "source": "test",
        "note": {
            "Definition": f"This is a test definition for {concept}",
            "Formula": "Test formula here",
            "Example": "Example calculation",
            "Use Case": "Common applications in finance"
        }
    })

@app.route('/seed', methods=['POST'])
def seed():
    data = request.json
    concept = data.get("concept", "Unknown")
    return jsonify({
        "source": "cached", 
        "concept": concept,
        "message": f"Concept '{concept}' seeded successfully"
    })

@app.route('/list', methods=['GET'])
def list_concepts():
    return jsonify([
        {
            "concept": "Sharpe Ratio",
            "source": "cached",
            "note": {
                "Definition": "Risk-adjusted return measure",
                "Formula": "(Return - Risk-free rate) / Standard deviation",
                "Example": "If portfolio returns 12% with 15% volatility and risk-free rate is 2%, Sharpe = (12-2)/15 = 0.67",
                "Use Case": "Comparing portfolio performance"
            }
        },
        {
            "concept": "Beta",
            "source": "cached",
            "note": {
                "Definition": "Measure of systematic risk relative to market",
                "Formula": "Covariance(asset, market) / Variance(market)",
                "Example": "Beta of 1.5 means 50% more volatile than market",
                "Use Case": "Asset pricing and risk assessment"
            }
        },
        {
            "concept": "Alpha",
            "source": "cached",
            "note": {
                "Definition": "Excess return over expected return given beta",
                "Formula": "Actual Return - [Risk-free rate + Beta × (Market return - Risk-free rate)]",
                "Example": "Positive alpha indicates outperformance",
                "Use Case": "Evaluating fund manager performance"
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