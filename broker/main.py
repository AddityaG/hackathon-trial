# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

# --- Internal Database and Models ---
# Simulating a database for agent registration and transaction storage
from agent_credentials import AGENT_CREDENTIALS, SCOPES_MAP

# In-memory storage for pending intents and proposals
# In a production app, this would be a persistent database (e.g., Firestore)
intents_db: Dict[str, Any] = {}
proposals_db: Dict[str, Any] = {}


class Token(BaseModel):
    """Pydantic model for the returned OAuth token."""
    access_token: str
    token_type: str


# --- OAuth 2.0 Configuration ---
# You would use a secure, randomly generated key in a real application
SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_agent_id(token: str = Depends(oauth2_scheme)):
    """Verifies the access token and returns the agent ID."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id: str = payload.get("sub")
        if agent_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return agent_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# --- Agent Protocol Models ---
class Intent(BaseModel):
    """Model for a consumer's loan intent."""
    transaction_id: str
    amount: float
    duration_months: int
    credit_score: str
    client_id: str


class Proposal(BaseModel):
    """Model for a bank's loan proposal."""
    transaction_id: str
    proposal_id: str
    bank_id: str
    offered_amount: float
    interest_rate: float
    terms: str


# --- FastAPI Application ---
app = FastAPI()

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth 2.0 Client Credentials Grant.
    Agents use their client_id and client_secret to get a short-lived access token.
    """
    # Look up the agent's credentials in our simulated database
    agent_id = form_data.username
    client_secret = form_data.password
    if agent_id not in AGENT_CREDENTIALS or AGENT_CREDENTIALS[agent_id]["client_secret"] != client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client ID or secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create the access token with the agent's scopes
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    scopes = SCOPES_MAP.get(agent_id, [])
    access_token = create_access_token(
        data={"sub": agent_id, "scopes": scopes}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/submit_intent", tags=["Agent Protocol"])
async def submit_intent(intent: Intent, agent_id: str = Depends(get_current_agent_id)):
    """
    Endpoint for a Consumer Agent to submit a loan intent.
    Requires a valid access token with the "consumer:write" scope.
    """
    scopes = SCOPES_MAP.get(agent_id, [])
    if "consumer:write" not in scopes:
        raise HTTPException(status_code=403, detail="Not authorized to submit intents")
    
    # Store the intent in our in-memory DB
    intents_db[intent.transaction_id] = intent.model_dump()
    proposals_db[intent.transaction_id] = [] # Initialize proposals for this intent
    
    return {"status": "Intent received", "transaction_id": intent.transaction_id}


@app.post("/submit_proposal", tags=["Agent Protocol"])
async def submit_proposal(proposal: Proposal, agent_id: str = Depends(get_current_agent_id)):
    """
    Endpoint for a Bank Agent to submit a loan proposal.
    Requires a valid access token with the "bank:write" scope.
    """
    scopes = SCOPES_MAP.get(agent_id, [])
    if "bank:write" not in scopes:
        raise HTTPException(status_code=403, detail="Not authorized to submit proposals")
        
    transaction_id = proposal.transaction_id
    if transaction_id not in proposals_db:
        raise HTTPException(status_code=404, detail="Transaction ID not found")
        
    proposals_db[transaction_id].append(proposal.model_dump())
    
    return {"status": "Proposal received", "proposal_id": proposal.proposal_id}


@app.get("/get_proposals/{transaction_id}", tags=["Agent Protocol"])
async def get_proposals(transaction_id: str, agent_id: str = Depends(get_current_agent_id)):
    """
    Endpoint for a Consumer Agent to retrieve proposals for a given transaction.
    Requires a valid access token with the "consumer:read" scope.
    """
    scopes = SCOPES_MAP.get(agent_id, [])
    if "consumer:read" not in scopes:
        raise HTTPException(status_code=403, detail="Not authorized to read proposals")
        
    if transaction_id not in proposals_db:
        raise HTTPException(status_code=404, detail="Transaction ID not found")
        
    return proposals_db[transaction_id]

# The remaining logic (acceptance/rejection) will be built in later steps.

# To run the app, use: uvicorn main:app --reload
