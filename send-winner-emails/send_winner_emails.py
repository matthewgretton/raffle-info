#!/usr/bin/env python3
"""
Jubilee PTA Raffle Winner Email Notification Script

Sends congratulatory emails to raffle winners with their prize details.

Usage:
    python send_winner_emails.py winners.csv [--dry-run]
    
Options:
    --dry-run    Preview emails without sending (prints to console)
"""

import csv
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

SENDER_EMAIL = "raffle@jubileepta.org.uk"
SENDER_NAME = "Jubilee PTA Raffle"

# Gmail SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Path to raffle-tracker.html (relative to this script's parent directory)
TRACKER_HTML_PATH = Path(__file__).parent.parent / "raffle-tracker.html"

# Better prize descriptions (donor -> detailed description)
PRIZE_DESCRIPTIONS = {
    "Basement 144": "5-hour venue hire (worth £750)",
    "Hyatt Hotel": "2 nights in deluxe king with breakfast (worth £700)",
    "Architecture for the Senses": "Design workshop & site visit (worth £600)",
    "F45 Dalston": "3-month membership (worth £580)",
    "Oblix - The Shard": "Three-course dinner with wine for two (worth £350)",
    "Instagym": "3 months platinum membership (worth £300)",
    "The Organised Curator": "Organising session (worth £150-£300)",
    "Imogen Love": "Private sound bath for 4 at N16 studio (worth £280)",
    "Blok Clapton": "10 premium class pack (worth £235)",
    "Tempo Dance": "1 week dance camp (worth £225)",
    "1 Hotel Mayfair": "60-minute massage (worth £180)",
    "Funn Clubb": "1 week holiday club - Feb half term (worth £175)",
    "Desi Dolls": "Toys (Islamic faith) (worth £160)",
    "NTS": "Clothing & merch bundle (worth £150)",
    "Dulcie (formerly Haekels)": "100ml fragrance (worth £140)",
    "Simply Circus": "2-day holiday camp pass (worth £130)",
    "We Are Worm": "Wreath (worth £120)",
    "Tom Foolery": "Voucher (£125)",
    "Calong": "Meal voucher (£100)",
    "Tako": "Dining voucher (£100)",
    "Whole Foods": "Goodie bag (approx £100)",
    "Londis N16": "Gift hamper (approx £93)",
    "Studio 58 London": "Haircut (worth £90)",
    "Carol Joy London": "Beauty bar skincare set (worth £80)",
    "Clapton Country Club": "Meal for two with a bottle of wine (worth £80)",
    "Karv": "Meal for two (worth £80)",
    "Mudra Yoga": "5-class pass (worth £70)",
    "EartH Hackney": "Pair of tickets (worth £60)",
    "Corrochios": "Voucher (£60)",
    "Pilates-Me": "1-month intro pass (worth £55)",
    "King Frank": "2-course meal for 2 with a bottle of wine (worth £55)",
    "Simply Hair": "Haircut (worth £55)",
    "Stokey Bears": "1-month unlimited breakfast (worth £50)",
    "Carmela's Pizzeria": "Voucher (£50)",
    "Clissold Park Tavern": "Voucher (£50)",
    "Escocesa": "Voucher (£50)",
    "Hilda": "Voucher (£50)",
    "Wheat": "Voucher (£50)",
    "Fleury Food Co.": "4-person celebration hamper (worth £45)",
    "Little Angel Theatre": "Family ticket to a show (worth £44)",
    "JR Innovative Building": "Voucher (£40)",
    "Prep Cookshop": "Cooking accessories (worth £40)",
    "Yum Yums": "Meal voucher (£40)",
    "Hidden Kitchen": "Meal voucher (£35)",
    "The Good Egg": "Babka voucher (£35)",
    "Stoke Newington Bookshop": "Book voucher (£30)",
    "The Axe Pub": "Food & drink voucher (£30)",
    "Kitchen Provisions": "Goodie bag (approx £30)",
    "Suba": "Brunch for two (worth £30)",
    "Ryan's N16": "Voucher (£25)",
    "Esters": "Café/bakery voucher (£25)",
    "Willy's Pies": "Voucher for 12 handheld pies (£25)",
    "The Little Wine Shop": "Voucher (£25)",
    "Biancas": "Two glasses of sparkling wine (approx £25)",
    "Jolley's": "Men's grooming package (worth £22.50)",
    "Jollein": "Online voucher (£20)",
    "Nando's": "Voucher (£20)",
    "Peach's": "5 free drinks (approx £20)",
    "The Dusty Knuckle": "Bread & pastries (worth £15)",
    "Shrine to the Vine": "Bottle of wine (approx £15)",
    "Hailey's Nails": "Nail polish voucher (£10)",
    "Allpress": "Coffee & pastry (approx £7.50)",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_email(email):
    """
    Validate an email address looks sensible.
    Returns (is_valid, warning_message)
    """
    warnings = []
    
    # Basic format check
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return False, "Invalid email format"
    
    # Check for common typos in TLDs
    typo_tlds = {
        '.con': '.com',
        '.cmo': '.com', 
        '.ocm': '.com',
        '.co,': '.com',
        '.cm': '.com',
        '.cok': '.co.uk',
        '.couk': '.co.uk',
        '.co.ik': '.co.uk',
        '.gmai.com': '.gmail.com',
        '.gmial.com': '.gmail.com',
        '.gmal.com': '.gmail.com',
        '.hotmal.com': '.hotmail.com',
        '.hotmai.com': '.hotmail.com',
    }
    
    email_lower = email.lower()
    for typo, correct in typo_tlds.items():
        if email_lower.endswith(typo):
            return False, f"Likely typo: '{typo}' should probably be '{correct}'"
    
    # Check for suspicious patterns
    if '..' in email:
        return False, "Contains double dots"
    
    if email.count('@') > 1:
        return False, "Contains multiple @ symbols"
    
    return True, None


def get_total_raised_from_tracker():
    """
    Parse the raffle-tracker.html file to get the current amount raised.
    Looks for: const CURRENT_AMOUNT = XXX;
    """
    try:
        with open(TRACKER_HTML_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the JavaScript variable
        match = re.search(r'const CURRENT_AMOUNT\s*=\s*(\d+)', content)
        if match:
            return int(match.group(1))
        else:
            print("⚠️  Warning: Could not find CURRENT_AMOUNT in raffle-tracker.html")
            return None
    except FileNotFoundError:
        print(f"⚠️  Warning: Could not find {TRACKER_HTML_PATH}")
        return None


def parse_prize(prize_string):
    """
    Parse prize string like "Basement 144 – 5-hour venue hire – £750"
    into components: donor, description, value
    
    Returns dict with: donor, description, value, value_numeric
    """
    # Handle en-dash (–) surrounded by spaces - this is the delimiter
    # Don't split on regular hyphens as they appear within words like "5-hour"
    parts = re.split(r'\s+–\s+', prize_string)
    
    if len(parts) >= 3:
        donor = parts[0].strip()
        # Value is typically the last part starting with £
        value = parts[-1].strip()
        # Description is everything in between
        description = ' – '.join(parts[1:-1]).strip()
    elif len(parts) == 2:
        donor = parts[0].strip()
        description = ""
        value = parts[1].strip()
    else:
        donor = prize_string
        description = ""
        value = ""
    
    # Extract numeric value
    value_match = re.search(r'£([\d,]+(?:\.\d{2})?)', value)
    value_numeric = float(value_match.group(1).replace(',', '')) if value_match else 0
    
    return {
        'donor': donor,
        'description': description,
        'value': value,
        'value_numeric': value_numeric,
        'full': prize_string
    }


def create_email_content(winner_name, prize_info, total_raised):
    """
    Create the email subject and body for a winner.
    Returns subject, plain_text_body, html_body
    """
    # Format the total raised nicely
    total_str = f"£{total_raised:,}" if total_raised else "over £700"
    
    first_name = winner_name.split()[0]
    
    # Use better description from lookup if available
    donor = prize_info['donor']
    if donor in PRIZE_DESCRIPTIONS:
        prize_desc = PRIZE_DESCRIPTIONS[donor]
    else:
        prize_desc = prize_info['description'] if prize_info['description'] else donor
    
    subject = f"🎉 Jubilee Raffle Winner - {donor}"
    
    # Plain text version
    plain_body = f"""Hi {first_name},

Great news, you're a winner! 🎉

Your prize:
    {donor} – {prize_desc}

If you are certain you will use your prize, please let us know by responding to this email.

Many prizes can be sent by email. For those that need to be picked up, someone from the Raffle team will be at the Cazenove entrance at drop off on Monday, Tuesday and Thursday.

If we haven't heard from you by Friday 12th December, we'll assume you don't want the prize and it will be re-entered into the draw so another family can enjoy it.

Thanks for taking part - together we raised a staggering {total_str} towards the KS2 playground!

This email is your proof of winning.

Best wishes,
Raffle Team
"""
    
    # HTML version - with prize box, all content in one flow
    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
<p>Hi {first_name},</p>
<p><strong>Great news, you're a winner!</strong> 🎉</p>
<p style="background: #f0f7ff; border-left: 4px solid #4a90e2; padding: 15px 20px; margin: 15px 0; border-radius: 4px;"><span style="font-size: 12px; color: #666;">YOUR PRIZE</span><br><strong style="font-size: 18px;">{donor}</strong><br><span style="color: #666;">{prize_desc}</span></p>
<p>If you are certain you will use your prize, please let us know by <strong>responding to this email</strong>.</p>
<p>Many prizes can be sent by email. For those that need to be picked up, someone from the Raffle team will be at the Cazenove entrance at drop off on Monday, Tuesday and Thursday.</p>
<p>If we haven't heard from you by <strong>Friday 12th December</strong>, we'll assume you don't want the prize and it will be re-entered into the draw so another family can enjoy it.</p>
<p>Thanks for taking part - together we raised a staggering <strong>{total_str}</strong> towards the KS2 playground!</p>
<p><strong>This email is your proof of winning.</strong></p>
<p>Best wishes,<br><strong>Raffle Team</strong></p>
</body>
</html>"""
    
    return subject, plain_body, html_body


def load_winners(csv_path):
    """
    Load winners from CSV file.
    Expected columns: Prizes, Winning Ticket, Winner Name, Winner Email, Winner Phone
    """
    winners = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prize_info = parse_prize(row['Prizes'])
            winners.append({
                'name': row['Winner Name'].strip(),
                'email': row['Winner Email'].strip(),
                'phone': row.get('Winner Phone', '').strip(),
                'ticket': row['Winning Ticket'].strip(),
                'prize': prize_info
            })
    
    return winners


def send_email(recipient_email, recipient_name, subject, plain_body, html_body, smtp_user, smtp_password, dry_run=False):
    """
    Send an email to a single recipient with both plain text and HTML versions.
    """
    if dry_run:
        print(f"\n{'='*60}")
        print(f"TO: {recipient_name} <{recipient_email}>")
        print(f"SUBJECT: {subject}")
        print(f"{'='*60}")
        print(plain_body)
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = f"{recipient_name} <{recipient_email}>"
        msg['Reply-To'] = SENDER_EMAIL
        
        # Plain text version (fallback)
        msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
        # HTML version (preferred)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"❌ Failed to send to {recipient_email}: {e}")
        return False


def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python send_winner_emails.py <winners.csv> [--dry-run] [--test] [--yes]")
        print("\nOptions:")
        print("  --dry-run    Preview full emails without sending")
        print("  --test       Just list who would be emailed (quick check)")
        print("  --yes        Skip confirmation prompt")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    test_mode = '--test' in sys.argv
    skip_confirm = '--yes' in sys.argv
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Get credentials (skip for dry run)
    smtp_user = None
    smtp_password = None
    
    if not dry_run and not test_mode:
        smtp_user = os.environ.get('GMAIL_USER')
        smtp_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not smtp_user or not smtp_password:
            print("❌ Error: Missing email credentials.")
            print("\nSet these environment variables:")
            print("  export GMAIL_USER='your-email@gmail.com'")
            print("  export GMAIL_APP_PASSWORD='your-app-password'")
            print("\nOr run with --dry-run to preview emails.")
            sys.exit(1)
    
    # Get total raised from tracker
    total_raised = get_total_raised_from_tracker()
    if total_raised:
        print(f"💰 Total raised (from tracker): £{total_raised:,}")
    
    # Load winners
    print(f"📂 Loading winners from: {csv_path}")
    winners = load_winners(csv_path)
    print(f"📋 Found {len(winners)} winners")
    
    # Calculate total prize value
    total_prize_value = sum(w['prize']['value_numeric'] for w in winners)
    print(f"🎁 Total prize value: £{total_prize_value:,.2f}")
    
    # Validate all email addresses
    print(f"\n📧 Validating email addresses...")
    invalid_emails = []
    valid_winners = []
    
    for winner in winners:
        is_valid, warning = validate_email(winner['email'])
        if is_valid:
            valid_winners.append(winner)
        else:
            invalid_emails.append({
                'name': winner['name'],
                'email': winner['email'],
                'prize': winner['prize']['full'],
                'warning': warning
            })
    
    if invalid_emails:
        print(f"\n⚠️  Found {len(invalid_emails)} problematic email(s):\n")
        for item in invalid_emails:
            print(f"  ❌ {item['name']}")
            print(f"     Email: {item['email']}")
            print(f"     Issue: {item['warning']}")
            print(f"     Prize: {item['prize']}")
            print()
        
        print(f"These {len(invalid_emails)} winner(s) will be SKIPPED.")
        print(f"Fix the emails in your CSV and re-run, or contact them manually.\n")
    
    print(f"✅ {len(valid_winners)} valid email(s) ready to send")
    
    # Test mode - just list recipients and exit
    if test_mode:
        print("\n" + "="*60)
        print("TEST MODE - Recipients who would be emailed:")
        print("="*60 + "\n")
        for i, winner in enumerate(valid_winners, 1):
            prize_desc = winner['prize']['description'] or winner['prize']['donor']
            print(f"{i:3}. {winner['name']}")
            print(f"     📧 {winner['email']}")
            print(f"     🎁 {prize_desc} ({winner['prize']['value']})")
            print()
        print("="*60)
        print(f"Total: {len(valid_winners)} emails would be sent")
        print("="*60)
        sys.exit(0)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No emails will be sent\n")
        winners = valid_winners  # Only show valid ones in dry run
    else:
        print(f"\n📧 Sending emails from: {SENDER_EMAIL}")
        if not skip_confirm:
            confirm = input(f"\nSend {len(valid_winners)} emails? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                sys.exit(0)
        else:
            print(f"\n⚡ Sending {len(valid_winners)} emails (--yes flag used)...\n")
        winners = valid_winners
    
    # Send emails
    sent = 0
    failed = 0
    
    for i, winner in enumerate(winners, 1):
        subject, plain_body, html_body = create_email_content(
            winner['name'],
            winner['prize'],
            total_raised
        )
        
        if not dry_run:
            print(f"[{i}/{len(winners)}] Sending to {winner['name']} ({winner['email']})...", end=" ")
        
        success = send_email(
            winner['email'],
            winner['name'],
            subject,
            plain_body,
            html_body,
            smtp_user,
            smtp_password,
            dry_run
        )
        
        if success:
            sent += 1
            if not dry_run:
                print("✅")
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total winners: {len(winners)}")
    if dry_run:
        print(f"Emails previewed: {sent}")
    else:
        print(f"Emails sent: {sent}")
        print(f"Emails failed: {failed}")


if __name__ == '__main__':
    main()

