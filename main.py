from fastapi import FastAPI, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
import os
import shutil
from typing import List
from datetime import datetime, timezone

from database import SessionLocal, init_db, Participant, Input, Solution, Result
from utils import verify_token, normalise_name, save_file, get_token
from judge0 import submit_to_judge0, LANG_MAP

app = FastAPI()
init_db()

templates = Jinja2Templates(directory="templates")

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    participants = db.query(Participant).all()
    # Days 1 to 25
    days = list(range(1, 26))
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "days": days,
            "participants": participants,
            "token": token
        }
    )

@app.get("/day/{day}", response_class=HTMLResponse)
async def day_view(day: int, request: Request, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    if not (1 <= day <= 25):
        raise HTTPException(status_code=404, detail="Day not found")
    
    participants = db.query(Participant).all()
    
    # Leaderboards logic
    # Rank by average time of most recent run for each input
    def get_leaderboard(part: int):
        # Subquery to get latest result for each (solution, input) pair
        # Actually, user wants "averaged across the most recent run for each input" for a solution.
        # So for a given solution, we find all inputs for that day. 
        # For each input, we find the latest Result for this solution.
        # Then average those.
        
        solutions = db.query(Solution).filter(Solution.day == day, Solution.part == part).all()
        board = []
        for sol in solutions:
            inputs = db.query(Input).filter(Input.day == day).all()
            times = []
            for inp in inputs:
                latest_res = db.query(Result).filter(Result.solution_id == sol.id, Result.input_id == inp.id)\
                    .order_by(Result.timestamp.desc()).first()
                if latest_res and latest_res.status == "Accepted":
                    times.append(latest_res.execution_time)
            
            avg_time = sum(times) / len(times) if times else None
            board.append({
                "participant": sol.participant.name,
                "avg_time": avg_time,
                "num_inputs": len(times),
                "total_inputs": len(inputs),
                "sol_id": sol.id
            })
        
        # Sort by avg_time, putting None values at the end
        return sorted(board, key=lambda x: (x["avg_time"] is None, x["avg_time"]))

    leaderboard1 = get_leaderboard(1)
    leaderboard2 = get_leaderboard(2)
    
    return templates.TemplateResponse(
        request=request, 
        name="day.html", 
        context={
            "day": day,
            "participants": participants,
            "leaderboard1": leaderboard1,
            "leaderboard2": leaderboard2,
            "token": token
        }
    )

@app.post("/submit/input")
async def submit_input(
    day: int = Form(...),
    participant_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    norm_name = normalise_name(participant_name)
    participant = db.query(Participant).filter(Participant.normalised_name == norm_name).first()
    if not participant:
        participant = Participant(name=participant_name, normalised_name=norm_name)
        db.add(participant)
        db.commit()
        db.refresh(participant)
    
    # Check if participant already has an input for this day (frontend constraint)
    # Backend allows multiple, but we can enforce "one per person per day" if that's the intent.
    # The prompt says: "The backend should support more than one inputs per day but the frontend should only allow people to submit one input per day."
    # I'll interpret this as: many people can submit inputs, and they all contribute to the testing.
    
    file_path = f"data/{norm_name}/input/day-{day:02d}"
    content = await file.read()
    save_file(content, file_path)
    
    # Store in DB if not already there
    existing_input = db.query(Input).filter(Input.participant_id == participant.id, Input.day == day).first()
    if not existing_input:
        new_input = Input(participant_id=participant.id, day=day, file_path=file_path)
        db.add(new_input)
    else:
        existing_input.timestamp = datetime.now(timezone.utc) # Update timestamp if re-submitted
    
    db.commit()
    return RedirectResponse(url=f"/day/{day}?token={token}", status_code=303)

@app.post("/submit/solution")
async def submit_solution(
    day: int = Form(...),
    part: int = Form(...),
    participant_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    norm_name = normalise_name(participant_name)
    participant = db.query(Participant).filter(Participant.normalised_name == norm_name).first()
    if not participant:
        participant = Participant(name=participant_name, normalised_name=norm_name)
        db.add(participant)
        db.commit()
        db.refresh(participant)
    
    sol_uuid = str(uuid.uuid4())
    ext = file.filename.split(".")[-1]
    if ext not in LANG_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    
    file_path = f"data/{norm_name}/solutions/{sol_uuid}.{ext}"
    content = await file.read()
    save_file(content, file_path)
    
    new_sol = Solution(
        participant_id=participant.id,
        day=day,
        part=part,
        file_path=file_path,
        language_id=LANG_MAP[ext],
        uuid=sol_uuid
    )
    db.add(new_sol)
    db.commit()
    
    return RedirectResponse(url=f"/day/{day}?token={token}", status_code=303)

@app.post("/run/{sol_id}")
async def run_solution(
    sol_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    sol = db.query(Solution).filter(Solution.id == sol_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solution not found")
    
    # Get all inputs for this day
    inputs = db.query(Input).filter(Input.day == sol.day).all()
    
    with open(sol.file_path, "r") as f:
        code = f.read()
    
    for inp in inputs:
        with open(inp.file_path, "r") as f:
            stdin = f.read()
        
        try:
            res = await submit_to_judge0(code, sol.language_id, stdin)
            new_res = Result(
                solution_id=sol.id,
                input_id=inp.id,
                execution_time=res["time"],
                status=res["status"],
                stdout=res["stdout"],
                stderr=res["stderr"]
            )
            db.add(new_res)
        except Exception as e:
            # Handle Judge0 errors
            new_res = Result(
                solution_id=sol.id,
                input_id=inp.id,
                status="Internal Error",
                stderr=str(e)
            )
            db.add(new_res)
            
    db.commit()
    return RedirectResponse(url=f"/day/{sol.day}?token={token}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
