"""
Terms and Conditions Service
Manages T&Cs display and acceptance for the platform
"""

TERMS_AND_CONDITIONS = """
*TERMS AND CONDITIONS OF SERVICE*

By using this Platform, you agree to be bound by these Terms.

*7.1 KEY DEFINITIONS*
- Platform: This legal services platform
- Legal Practitioner: Registered attorney under Legal Practitioners Act
- Law Firm: Registered firm with Law Society of Zimbabwe
- Client: User submitting legal matters through the Platform
- 72-Hour Rule: SLA requiring response within 72 hours of payment

*7.2 ELIGIBILITY*
- Law Firms must be in good standing with LSZ
- Practitioners must be authorized by their law firm
- Clients must provide truthful information

*7.3 ADMINISTRATION FEE*
- Each submission requires USD$5.00 fee
- Payment via Paynow (EcoCash, OneMoney, Visa, Mastercard)
- Fee is non-refundable except on 72-hour default

*7.4 PAYMENT ALLOCATION*
- USD$3.00 (60%) to Platform administration costs
- USD$2.00 (40%) to Escrow Vault for attending lawyer
- Escrow released on successful completion

*7.5 CONFIDENTIALITY & SECURITY*
- Your dossier is encrypted and secure
- Access restricted to authorized users only
- Audit trail maintained for all activities

*7.6 72-HOUR RULE*
- Timer starts on payment confirmation
- Lawyer must respond within 72 hours
- Default triggers full refund and reassignment

*7.7 CONFLICT OF INTEREST*
- Platform performs mandatory conflict checks
- Assignment blocked if conflict detected

*7.8 FUTURE CRIME EXCEPTION*
- Platform detects intent to commit serious crimes
- Attorney-client privilege bypassed for public safety
- Matter routed to reporting authorities

*7.9 LIABILITY DISCLAIMER*
- Platform provides drafting support only
- Not substitute for legal advice from practitioner
- Platform liability limited by law

*7.10 GOVERNING LAW*
- Governed by Zimbabwean law
- Including Legal Practitioners Act, Cyber and Data Protection Act

*By proceeding with payment, you accept these Terms.*
"""

def get_terms_summary() -> str:
    """Get abbreviated T&Cs for WhatsApp display"""
    return """
*TERMS SUMMARY* 📋

• Administration Fee: USD$5.00
• 72-Hour Response Guarantee
• Encrypted Secure Storage
• Conflict of Interest Checks
• Full Refund on Default

Full T&Cs available at: https://your-platform.com/terms

Reply 'ACCEPT' to agree and proceed with payment
Reply 'DECLINE' to cancel
"""

def get_full_terms() -> str:
    """Get complete T&Cs text"""
    return TERMS_AND_CONDITIONS
