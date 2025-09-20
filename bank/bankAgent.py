# bank_agent.py
import requests
import json
import time
from typing import Dict, Any
import uuid

# --- Agent Configuration ---
# Your unique client ID and secret for this Bank Agent
CLIENT_ID = "bank_agent_a"
CLIENT_SECRET = "bank_secret_a"

# Broker API endpoints
BROKER_BASE_URL = "http://127.0.0.1:8000"
TOKEN_URL = f"{BROKER_BASE_URL}/token"
GET_INTENTS_URL = f"{BROKER_BASE_URL}/get_intents"
SUBMIT_PROPOSAL_URL = f"{BROKER_BASE_URL}/submit_proposal"


def get_access_token() -> str:
    """
    Authenticates with the broker and returns a valid access token.
    """
    payload = {
        "grant_type": "client_credentials",
        "username": CLIENT_ID,
        "password": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return ""


def process_intent(intent: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Simulates a bank's internal process to assess a loan intent
    and generate a proposal.
    """
    print(f"\nProcessing intent for transaction ID: {intent['transaction_id']}")
    
    # --- Simulated LLM/Decision Logic ---
    # This is where a real LLM agent would perform a complex credit assessment.
    # For now, we'll use simple rules based on credit score.
    credit_score = intent.get("credit_score", "poor")
    loan_amount = intent.get("amount", 0.0)
    
    if credit_score == "good":
        interest_rate = 0.05
        terms = "5% APR, excellent credit offer"
        offered_amount = loan_amount
    elif credit_score == "fair":
        interest_rate = 0.10
        terms = "10% APR, standard offer"
        offered_amount = loan_amount
    elif credit_score == "poor":
        # A bank might not offer a loan for a poor credit score
        print(f"Credit score is poor. No proposal will be made.")
        return None
    else:
        # Unknown credit score, apply high risk terms
        interest_rate = 0.15
        terms = "15% APR, high-risk offer"
        offered_amount = loan_amount
        
    proposal = {
        "transaction_id": intent["transaction_id"],
        "proposal_id": str(uuid.uuid4()),
        "bank_id": CLIENT_ID,
        "offered_amount": offered_amount,
        "interest_rate": interest_rate,
        "terms": terms
    }
    
    return proposal


def submit_proposal(access_token: str, proposal: Dict[str, Any]):
    """
    Submits a loan proposal to the broker.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(SUBMIT_PROPOSAL_URL, json=proposal, headers=headers)
        response.raise_for_status()
        print(f"Successfully submitted proposal for transaction: {proposal['transaction_id']}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to submit proposal: {e}")


def main():
    """Main function to run the Bank Agent logic."""
    print("Bank Agent starting...")
    access_token = get_access_token()
    if not access_token:
        print("Could not get access token. Exiting.")
        return

    print("Agent is running and waiting for new intents...")
    
    while True:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(GET_INTENTS_URL, headers=headers)
            response.raise_for_status()
            intents = response.json()
            
            if intents:
                print(f"Found {len(intents)} new intents. Processing...")
                for intent in intents:
                    proposal = process_intent(intent)
                    if proposal:
                        submit_proposal(access_token, proposal)
            else:
                print("No new intents found. Polling again in 5 seconds...")
                
            time.sleep(5) # Poll every 5 seconds
            
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while communicating with the broker: {e}")
            print("Attempting to get a new token and retry in 10 seconds.")
            access_token = get_access_token()
            time.sleep(10)


if __name__ == "__main__":
    main()
