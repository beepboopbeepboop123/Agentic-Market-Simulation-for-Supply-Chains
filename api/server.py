from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Add the parent directory to the path so we can import our simulation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your simulation engine and multi-agent system
from simulation.engine import run_monte_carlo
from agents.multi_agent import run_multi_agent_system

app = FastAPI(title="Supply Chain War Room API")

# Enable CORS for Flutter/Web testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Flutter app to connect
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

# Define the exact data structure the Flutter app will send to us
class SimulationRequest(BaseModel):
    disaster_node: str
    source_node: str
    target_node: str
    runs: int = 1000

@app.get("/")
def read_root():
    return {"status": "Agentic Simulation Engine is Online"}

@app.post("/simulate")
def trigger_simulation(request: SimulationRequest):
    try:
        # Step 1: Run the Mathematical Simulation (Monte Carlo)
        print(f"\n[API] Running {request.runs} simulations for {request.disaster_node}...")
        math_result = run_monte_carlo(
            closed_node=request.disaster_node,
            source=request.source_node,
            target=request.target_node,
            runs=request.runs
        )
        
        if not math_result:
            raise HTTPException(status_code=404, detail="No recovery routes found.")
            
        # Step 2: Trigger the AI Agents to analyze the math result
        print(f"[API] Triggering 4-Agent Pipeline...")
        agent_result = run_multi_agent_system(
            disaster_node=request.disaster_node,
            source=request.source_node,
            target=request.target_node
        )
        
        # Step 3: Combine both outputs into one massive payload for Flutter
        return {
            "status": "success",
            "data": {
                "simulation_math": math_result,
                "ai_analysis": agent_result
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This runs the server locally on port 8000
    uvicorn.run(app, host="localhost", port=8000)