"""
Stripe payment integration for subscription management
"""
import os
import stripe
from typing import Dict, Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

stripe.api_key = os.environ.get('STRIPE_API_KEY', '')

# Subscription plan configurations
PLANS = {
    "basic": {
        "name": "Basic Plan",
        "price": 4900,  # $49.00 in cents
        "currency": "usd",
        "interval": "month",
        "features": ["sandata_submission"],
        "limits": {
            "max_timesheets": 100,
            "max_employees": 5,
            "max_patients": 10
        }
    },
    "professional": {
        "name": "Professional Plan",
        "price": 14900,  # $149.00 in cents
        "currency": "usd",
        "interval": "month",
        "features": ["sandata_submission", "evv_submission", "bulk_operations", "advanced_reporting"],
        "limits": {
            "max_timesheets": -1,  # Unlimited
            "max_employees": -1,
            "max_patients": -1
        }
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "price": None,  # Custom pricing
        "currency": "usd",
        "interval": "month",
        "features": ["sandata_submission", "evv_submission", "bulk_operations", "advanced_reporting", "api_access", "white_label"],
        "limits": {
            "max_timesheets": -1,
            "max_employees": -1,
            "max_patients": -1
        }
    }
}

def create_checkout_session(
    organization_id: str,
    plan: str,
    success_url: str,
    cancel_url: str,
    customer_email: Optional[str] = None
) -> Dict:
    """
    Create a Stripe checkout session for subscription
    
    Args:
        organization_id: The organization ID
        plan: Plan name (basic, professional, enterprise)
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled
        customer_email: Customer's email address
    
    Returns:
        Dict with session_id and url
    """
    if plan not in PLANS or plan == "enterprise":
        raise ValueError(f"Invalid plan: {plan}")
    
    plan_config = PLANS[plan]
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': plan_config['currency'],
                    'product_data': {
                        'name': plan_config['name'],
                        'description': f"{plan_config['name']} - {', '.join(plan_config['features'])}"
                    },
                    'recurring': {
                        'interval': plan_config['interval']
                    },
                    'unit_amount': plan_config['price'],
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
            client_reference_id=organization_id,
            metadata={
                'organization_id': organization_id,
                'plan': plan
            }
        )
        
        return {
            'session_id': session.id,
            'url': session.url
        }
    except Exception as e:
        raise Exception(f"Failed to create checkout session: {str(e)}")

def create_billing_portal_session(customer_id: str, return_url: str) -> Dict:
    """
    Create a Stripe billing portal session
    
    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to after managing billing
    
    Returns:
        Dict with url
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        
        return {'url': session.url}
    except Exception as e:
        raise Exception(f"Failed to create billing portal session: {str(e)}")

def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict:
    """
    Verify Stripe webhook signature
    
    Args:
        payload: Raw request body
        sig_header: Stripe-Signature header
    
    Returns:
        Parsed event object
    """
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError as e:
        raise ValueError("Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise ValueError("Invalid signature")

def get_plan_limits(plan: str) -> Dict:
    """Get the limits for a specific plan"""
    if plan in PLANS:
        return PLANS[plan]['limits']
    return PLANS['basic']['limits']  # Default to basic

def get_plan_features(plan: str) -> list:
    """Get the features for a specific plan"""
    if plan in PLANS:
        return PLANS[plan]['features']
    return PLANS['basic']['features']  # Default to basic
