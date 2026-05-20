import httpx
import asyncio
import base64

JUDGE0_URL = "http://localhost:2358"

# Mapping extensions to Judge0 language IDs (v1.13.1-extra)
# Python: 71, Rust: 73, C++ (GCC 9.2.0): 54
# We can expand this as needed.
LANG_MAP = {
    "py": 71,
    "rs": 73,
    "cpp": 54,
    "cc": 54,
    "cxx": 54,
    "c++": 54,
    "c": 48,
    "js": 63,
    "ts": 74,
    "go": 60,
}

async def submit_to_judge0(source_code: str, language_id: int, stdin: str = ""):
    async with httpx.AsyncClient() as client:
        payload = {
            "source_code": base64.b64encode(source_code.encode()).decode(),
            "language_id": language_id,
            "stdin": base64.b64encode(stdin.encode()).decode(),
            "base64_encoded": True
        }
        
        response = await client.post(f"{JUDGE0_URL}/submissions?base64_encoded=true&wait=false", json=payload)
        if response.status_code != 201:
            raise Exception(f"Judge0 error: {response.text}")
        
        token = response.json().get("token")
        
        # Poll for results
        while True:
            res_resp = await client.get(f"{JUDGE0_URL}/submissions/{token}?base64_encoded=true")
            result = res_resp.json()
            status_id = result.get("status", {}).get("id")
            
            if status_id not in [1, 2]: # 1: In Queue, 2: Processing
                break
            
            await asyncio.sleep(0.5)
            
        # Decode results
        stdout = base64.b64decode(result.get("stdout") or "").decode() if result.get("stdout") else ""
        stderr = base64.b64decode(result.get("stderr") or "").decode() if result.get("stderr") else ""
        compile_output = base64.b64decode(result.get("compile_output") or "").decode() if result.get("compile_output") else ""
        
        return {
            "stdout": stdout,
            "stderr": stderr + compile_output,
            "status": result.get("status", {}).get("description"),
            "time": float(result.get("time") or 0.0)
        }
