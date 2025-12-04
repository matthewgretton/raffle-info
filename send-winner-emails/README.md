# Raffle Winner Email Notification Script

Sends congratulatory emails to raffle winners with their prize details.

## Setup

### 1. Gmail App Password

Since you're sending from `raffle@jubileepta.org.uk` via Gmail:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication (if not already)
3. Go to **App passwords** (search for it in Google Account)
4. Create a new app password for "Mail"
5. Copy the 16-character password

### 2. Set Environment Variables

```bash
export GMAIL_USER='your-personal-gmail@gmail.com'  # The account with send-as permission
export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'    # The app password from step 1
```

Or create a `.env` file (don't commit this!):
```
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

Then source it: `source .env` or use a tool like `python-dotenv`.

## Usage

### Preview emails (dry run)

```bash
python send_winner_emails.py /path/to/winners.csv --dry-run
```

This will print all emails to the console without sending anything.

### Send emails

```bash
python send_winner_emails.py /path/to/winners.csv
```

You'll be asked to confirm before emails are sent.

## CSV Format

Expected columns:
- `Prizes` - Prize description (e.g., "Basement 144 – 5-hour venue hire – £750")
- `Winning Ticket` - Ticket number
- `Winner Name` - Full name
- `Winner Email` - Email address
- `Winner Phone` - Phone number (optional)

## How It Works

1. Parses the winners CSV
2. Reads `raffle-tracker.html` to get the current amount raised
3. For each winner, sends a personalized email with:
   - Their prize details (donor, description, value)
   - Instructions for claiming
   - Thank you message with total raised

## Testing

Create a test CSV with your own email addresses to test first:

```csv
Prizes,Winning Ticket,Winner Name,Winner Email,Winner Phone
Test Prize – A test item – £50,001,Your Name,your@email.com,1234567890
Another Test – Something nice – £25,002,Your Name,your@email.com,1234567890
```

## Troubleshooting

### "Authentication failed"
- Make sure you're using an App Password, not your regular password
- Verify the GMAIL_USER has "Send as" permission for raffle@jubileepta.org.uk

### "Could not find CURRENT_AMOUNT"
- Make sure `raffle-tracker.html` exists in the parent directory
- Check that it contains `const CURRENT_AMOUNT = XXX;`

### Emails going to spam
- This is common for bulk emails
- Winners can add raffle@jubileepta.org.uk to contacts
- Consider sending in smaller batches

