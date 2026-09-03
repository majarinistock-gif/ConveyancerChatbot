# WhatsApp Conveyancing Bot for Zimbabwe

A comprehensive WhatsApp chatbot for Zimbabwean property owners seeking conveyancing services, featuring automated OCR document processing, multi-application state management, and Paynow payment integration.

## Features

- **7 Conveyancing Services**: Deed of Transfer, Deeds Office Search, Certificate of Registered Title (CRT), Deed of Partition, Deed of Exchange, Deed of Rectification, and Deed of Grant
- **Automated OCR Processing**: Extracts data from Zimbabwean ID documents using OCR.space API
- **Multi-Application Management**: Handle multiple applications per user with resume functionality
- **Payment Integration**: $5 USD admin fee via Paynow (EcoCash, InnBucks, OneMoney)
- **Document Validation**: Service-specific file format requirements and validation
- **Paginated Law Firm Selection**: Choose from 20 conveyancers with alphabetical pagination
- **Admin Dashboard API**: REST endpoints for application management and verification
- **MongoDB Storage**: Secure document storage with GridFS for files

## Technology Stack

- **Backend**: Python (FastAPI)
- **Database**: MongoDB Atlas (M0 Free Tier) with GridFS
- **Hosting**: Render.com (Free Tier)
- **External APIs**:
  - Meta WhatsApp Cloud API (Sandbox/Production)
  - OCR.space API (Free Tier: 25,000 requests/month)
  - Paynow Zimbabwe API

## Project Structure

```
whatsapp-conveyancing-bot/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── database.py               # MongoDB connection setup
│   ├── models.py                 # Database models
│   ├── webhook.py                # WhatsApp webhook handlers
│   ├── state_machine.py          # Conversation flow state management
│   ├── ocr_service.py            # OCR.space integration
│   ├── file_service.py           # File validation & storage
│   ├── token_manager.py          # Meta token management
│   ├── payment_service.py        # Paynow payment integration
│   ├── whatsapp_service.py       # WhatsApp API helpers
│   ├── document_sequences.py     # Service-specific document sequences
│   ├── conditional_logic.py      # Conditional document requirements
│   ├── law_firm_selection.py     # Law firm pagination & selection
│   ├── api.py                    # Admin API endpoints
│   └── payment_callback.py       # Payment callback handlers
├── tests/
│   └── __init__.py
├── main.py                       # FastAPI application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore
├── seed_data.py                  # Conveyancers data seeding script
└── README.md
```

## Installation

### Prerequisites

- Python 3.8+
- MongoDB Atlas account
- Meta Developer account
- OCR.space API key
- Paynow integration credentials

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whatsapp-conveyancing-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Set up MongoDB Atlas**
   - Create MongoDB Atlas account (M0 Free Tier)
   - Create database: `conveyancing_bot`
   - Create collections: `sessions`, `conveyancers`, `applications`
   - Enable GridFS for file storage
   - Add your MongoDB URI to `.env`

6. **Seed conveyancers data**
   ```bash
   python seed_data.py
   ```

7. **Set up Meta Developer Account**
   - Create Meta Developer account
   - Create WhatsApp Cloud API app in sandbox mode
   - Get Temporary Access Token, Phone Number ID, Test Phone Number
   - Add credentials to `.env`

## Configuration

### Environment Variables

```env
# Application Settings
ENVIRONMENT=sandbox
PORT=8000
DEBUG=true

# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/conveyancing_bot
MONGO_DATABASE=conveyancing_bot

# Meta WhatsApp Configuration (Sandbox Mode)
META_ACCESS_TOKEN=your_temporary_access_token
META_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_verify_token

# OCR.space Configuration
OCR_SPACE_API_KEY=your_ocr_space_api_key
OCR_SPACE_ENGINE=3

# Paynow Payment Configuration
PAYNOW_INTEGRATION_ID=your_paynow_integration_id
PAYNOW_INTEGRATION_KEY=your_paynow_integration_key
PAYNOW_RESULT_URL=https://your-app.onrender.com/api/payment/callback

# Application Settings
ADMIN_FEE_AMOUNT=5.00
ADMIN_FEE_CURRENCY=USD
SESSION_EXPIRY_HOURS=48

# File Upload Settings
MAX_FILE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png
ALLOWED_DOCUMENT_FORMATS=pdf

# Pagination Settings
CONVEYANCERS_PER_PAGE=5

# Webhook Configuration
WEBHOOK_URL=https://your-app.onrender.com/webhook
```

## Running the Application

### Development

```bash
python main.py
```

The application will start on `http://localhost:8000`

### Production Deployment

See the [Deployment Guide](#deployment) section for Render.com deployment instructions.

## API Endpoints

### Webhook Endpoints

- `GET /webhook` - Meta webhook verification
- `POST /webhook` - Main webhook message handler
- `GET /webhook/health` - Webhook health check

### Admin API Endpoints

- `GET /api/applications` - List all applications
- `GET /api/applications/{id}` - Get application details
- `PUT /api/applications/{id}/status` - Update verification status
- `GET /api/applications/{id}/documents` - Get document URLs
- `POST /api/applications/{id}/reject` - Reject with reason
- `GET /api/applications/{id}/payment` - Get payment information
- `GET /api/documents/{file_id}` - Retrieve stored document
- `GET /api/conveyancers` - List conveyancers
- `GET /api/stats` - Get application statistics
- `GET /api/health` - API health check

### Payment Callback Endpoints

- `POST /api/payment/callback` - Paynow payment status callback
- `GET /api/payment/return/{application_id}` - Payment return handler

## Available Services

1. **Deed of Transfer** - Transferring property ownership from seller to buyer
2. **Deeds Office Search** - Verifying property ownership, boundaries, and active bonds
3. **Certificate of Registered Title (CRT)** - Issuing independent title deed for subdivision
4. **Deed of Partition** - Splitting jointly owned property into separate titles
5. **Deed of Exchange** - Legal swap between two property owners
6. **Deed of Rectification** - Correcting errors on registered title deed
7. **Deed of Grant** - First-time title registration for state-allocated land

## Document Requirements

Each service has specific document requirements:

### Deed of Transfer
- Seller & Buyer IDs (OCR processed)
- Original Title Deed (PDF)
- Agreement of Sale (PDF)
- Power of Attorney (PDF)
- Declarations (PDF)
- CGT Clearance (PDF)
- Rates Clearance (PDF)
- Levy Clearance (PDF - conditional for sectional title)
- Marital Status Proof (PDF)

### Deeds Office Search
- Property Description (text input)
- Applicant ID (OCR processed)
- Prior Deed Number (optional text input)

### Certificate of Registered Title (CRT)
- Owner ID (OCR processed)
- Parent Title Deed (PDF)
- Subdivision Permit (PDF)
- Surveyor General Diagram (PDF)
- Certificate of Compliance (PDF)
- Section 40 Form (PDF)

### Deed of Partition
- All Joint Owners' IDs (OCR processed)
- Joint Title Deed (PDF)
- Partition Agreement (PDF)
- Subdivision Permit & SG Diagrams (PDF)
- CGT Assessment/Clearance (PDF)
- Rates Clearance (PDF)

### Deed of Exchange
- Owner A & B IDs (OCR processed)
- Both Title Deeds (PDF)
- Exchange Agreement (PDF)
- Two CGT Clearances (PDF)
- Two Rates Clearances (PDF)

### Deed of Rectification
- Owner ID (OCR processed)
- Erroneous Title Deed (PDF)
- Affidavit (PDF)
- Corrected SG Diagram (PDF - conditional)
- Rectification Form (PDF)

### Deed of Grant
- Grantee ID (OCR processed)
- Allocation/Offer Letter (PDF)
- Surveyor General Diagram (PDF)
- Ministry Clearance/Payment Proof (PDF)
- Draft Deed of Grant (PDF)

## Deployment

### Render.com Deployment

1. **Create Render.com account**
   - Sign up at [render.com](https://render.com)

2. **Prepare your repository**
   - Push your code to GitHub
   - Ensure `.env` is in `.gitignore`

3. **Create a new Web Service**
   - Connect your GitHub repository
   - Select "Python" as the runtime
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python main.py`

4. **Configure environment variables**
   - Add all variables from `.env.example` to Render's environment variables
   - Update `WEBHOOK_URL` and `PAYNOW_RESULT_URL` with your Render URL

5. **Deploy**
   - Click "Deploy Web Service"
   - Wait for deployment to complete

6. **Configure Meta Webhook**
   - Go to Meta Developer Dashboard
   - Set webhook URL to: `https://your-app.onrender.com/webhook`
   - Verify the webhook

## Production Upgrade Path

To move from sandbox to production:

1. **Verify Meta Business Account**
   - Gather business verification documents
   - Create and verify Meta Business Account
   - Submit for Meta review (1-5 business days)

2. **Set up WhatsApp Business Account (WABA)**
   - Verify business phone number via SMS
   - Submit WhatsApp API use case for approval

3. **Configure production environment**
   - Generate permanent System User access token
   - Update environment variables with production credentials
   - Remove test number limitations

4. **Migrate to production**
   - Backup existing sandbox data
   - Update webhook URL for production
   - Test production webhook connectivity
   - Monitor initial production API costs

## Troubleshooting

### Common Issues

**MongoDB Connection Failed**
- Check your MongoDB URI format
- Ensure IP whitelist includes your deployment IP
- Verify database user permissions

**Meta Token Expired**
- Sandbox tokens expire every 24 hours
- Use the `/api/token/health` endpoint to check token status
- Manually refresh token in Meta Developer Dashboard

**OCR Processing Failed**
- Check OCR.space API key is valid
- Verify image format is supported (JPG, PNG, PDF)
- Check API quota (25,000 requests/month free tier)

**Payment Processing Failed**
- Verify Paynow integration credentials
- Check phone number format (263XXXXXXXXX)
- Ensure Paynow result URL is accessible

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For support, please contact:
- Email: support@conveyancingbot.co.zw
- WhatsApp: +2637XXXXXXXXX

## Acknowledgments

- Meta WhatsApp Cloud API
- OCR.space for document processing
- Paynow Zimbabwe for payment integration
- MongoDB Atlas for database services