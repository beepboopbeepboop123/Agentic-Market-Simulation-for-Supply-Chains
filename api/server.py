from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add the parent directory to the path so we can import our simulation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing simulation engine
from simulation.engine import run_monte_carlo

app = FastAPI(title="Supply Chain War Room API")

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
        # Trigger your exact existing python function
        result = run_monte_carlo(
            closed_node=request.disaster_node,
            source=request.source_node,
            target=request.target_node,
            runs=request.runs
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="No recovery routes found.")
            
        return {"status": "success", "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This runs the server locally on port 8000
    uvicorn.run(app, host="localhost", port=8000)