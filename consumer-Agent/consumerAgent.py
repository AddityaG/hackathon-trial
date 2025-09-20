# consumer_agent.py
import requests
import json
import time
from typing import Dict, Any
import uuid

# --- Agent Configuration ---
# Your unique client ID and secret for the Consumer Agent
CLIENT_ID = "consumer_agent_1"
CLIENT_SECRET = "consumer_secret_1"

# Broker API endpoints
BROKER_BASE_URL = "http://127.0.0.1:8000"
TOKEN_URL = f"{BROKER_BASE_URL}/token"
SUBMIT_INTENT_URL = f"{BROKER_BASE_URL}/submit_intent"
GET_PROPOSALS_URL = f"{BROKER_BASE_URL}/get_proposals"


def get_access_token() -> str:
    """
    Authenticates with the broker using the Client Credentials Grant
    and returns a valid access token.
    """
    payload = {
        "grant_type": "client_credentials",
        "username": CLIENT_ID,
        "password": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return ""


def submit_loan_intent(access_token: str, amount: float, duration_months: int, credit_score: str) -> str:
    """
    Submits a loan intent to the broker on behalf of the consumer.
    Returns the transaction ID.
    """
    transaction_id = str(uuid.uuid4())
    intent_payload = {
        "transaction_id": transaction_id,
        "amount": amount,
        "duration_months": duration_months,
        "credit_score": credit_score,
        "client_id": CLIENT_ID,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(SUBMIT_INTENT_URL, json=intent_payload, headers=headers)
        response.raise_for_status()
        print(f"Loan intent submitted. Transaction ID: {transaction_id}")
        return transaction_id
    except requests.exceptions.RequestException as e:
        print(f"Failed to submit loan intent: {e}")
        return ""


def get_proposals(access_token: str, transaction_id: str) -> Dict[str, Any]:
    """
    Polls the broker for proposals for a given transaction ID.
    Returns the list of proposals.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(f"{GET_PROPOSALS_URL}/{transaction_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve proposals: {e}")
        return {}


def main():
    """Main function to run the Consumer Agent logic."""
    print("Consumer Agent starting...")
    access_token = get_access_token()
    if not access_token:
        print("Could not get access token. Exiting.")
        return

    # --- Simulate User Input ---
    print("\nPlease provide your loan request details:")
    amount = float(input("Loan amount: "))
    duration = int(input("Duration (in months): "))
    credit_score = input("Credit score (e.g., 'good', 'fair', 'poor'): ")

    # Submit the intent to the broker
    transaction_id = submit_loan_intent(access_token, amount, duration, credit_score)
    if not transaction_id:
        return

    # Poll for proposals
    print("\nWaiting for proposals from Bank Agents...")
    proposals = []
    retries = 0
    while not proposals and retries < 10:
        time.sleep(2)  # Wait 2 seconds before polling again
        proposals = get_proposals(access_token, transaction_id)
        if proposals:
            print("\nProposals received!")
            print(json.dumps(proposals, indent=2))
            break
        else:
            print("No proposals yet. Retrying...")
        retries += 1
    
    if not proposals:
        print("No proposals received. Exiting.")
        return
        
    # --- Decision Logic ---
    # In a full LLM-powered agent, this is where the LLM would analyze and compare offers.
    # For now, we'll use a simple logic to find the best offer.
    best_offer = None
    if proposals:
        best_offer = min(proposals, key=lambda x: x['interest_rate'])
        print("\n--- Best Offer ---")
        print(f"Bank: {best_offer['bank_id']}")
        print(f"Interest Rate: {best_offer['interest_rate'] * 100}%")
        print(f"Terms: {best_offer['terms']}")


if __name__ == "__main__":
    main()
