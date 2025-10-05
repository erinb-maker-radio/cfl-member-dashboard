"""
Member Dashboard Data Analyzer
===============================
Processes Zeffy payment data to generate member analytics

Usage:
    python analyze_members.py
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import glob

# Configuration
EXPORT_FOLDER = r'C:\Users\erin\Zeffy_Exports'
OUTPUT_FILE = r'C:\Users\erin\CFL Member Dashboard\dashboard_data.json'

def get_latest_export_file():
    """Find the most recent Zeffy export file"""
    export_path = Path(EXPORT_FOLDER)
    files = list(export_path.glob('zeffy-payments-*.csv'))

    if not files:
        raise FileNotFoundError(f"No export files found in {EXPORT_FOLDER}")

    # Sort by modification time, get most recent
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file

def categorize_membership(details):
    """Categorize membership type from payment details"""
    if pd.isna(details):
        return None

    details_lower = str(details).lower()

    if 'basic' in details_lower:
        return 'Basic'
    elif 'pro' in details_lower or 'professional' in details_lower:
        return 'Pro'
    elif 'volunteer' in details_lower:
        return 'Volunteer'
    else:
        return None  # Not a membership payment

def is_membership_payment(details):
    """Check if payment is a membership payment"""
    return categorize_membership(details) is not None

def analyze_payments(file_path):
    """Analyze payment data and generate dashboard metrics"""

    # Read Excel file
    df = pd.read_excel(file_path)

    print(f"Loaded {len(df)} payment records")
    print(f"Columns: {df.columns.tolist()}")

    # Convert date column to datetime
    # Adjust column name based on actual data
    date_col = 'Payment Date' if 'Payment Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Get current date and 60 days ago
    now = datetime.now()
    sixty_days_ago = now - timedelta(days=60)
    thirty_days_ago = now - timedelta(days=30)

    # Filter for successful payments only
    if 'Payment Status' in df.columns:
        df_success = df[df['Payment Status'].str.contains('Succeed', case=False, na=False)]
    else:
        df_success = df.copy()

    # Categorize memberships and filter only membership payments
    details_col = 'Details' if 'Details' in df.columns else 'Description'
    if details_col in df.columns:
        df_success['Membership Type'] = df_success[details_col].apply(categorize_membership)
        # Filter to only membership payments (not None)
        df_memberships = df_success[df_success['Membership Type'].notna()].copy()
    else:
        df_memberships = pd.DataFrame()  # No membership data

    print(f"Found {len(df_memberships)} membership payments out of {len(df_success)} total successful payments")

    # Get amount column
    amount_col = 'Total Amount' if 'Total Amount' in df.columns else 'Amount'

    # Find active members (paid in last 60 days) - only membership payments
    recent_payments = df_memberships[df_memberships[date_col] >= sixty_days_ago]

    # Get unique members (by email or contact)
    contact_col = 'Email' if 'Email' in df.columns else 'Contact'
    active_members = recent_payments[contact_col].nunique()

    # Count by membership type
    membership_counts = recent_payments.groupby('Membership Type')[contact_col].nunique().to_dict()

    # Calculate monthly revenue (last complete calendar month) - only memberships
    # Get first day of current month
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Get first day of last month
    if now.month == 1:
        last_month_start = current_month_start.replace(year=now.year - 1, month=12)
    else:
        last_month_start = current_month_start.replace(month=now.month - 1)

    # Get payments from last complete month only
    last_month_payments = df_memberships[
        (df_memberships[date_col] >= last_month_start) &
        (df_memberships[date_col] < current_month_start)
    ]
    monthly_revenue = last_month_payments[amount_col].sum() if amount_col in last_month_payments.columns else 0

    # Calculate revenue by membership type
    revenue_by_type = recent_payments.groupby('Membership Type')[amount_col].sum().to_dict() if amount_col in recent_payments.columns else {}

    # Find members who quit
    # Method 1: Has "Stopped" recurring status (cancelled but may still have access)
    recurring_col = 'Recurring Status' if 'Recurring Status' in df_memberships.columns else None
    stopped_members = set()
    if recurring_col:
        stopped_df = df_memberships[df_memberships[recurring_col].str.contains('Stopped', case=False, na=False)]
        stopped_members = set(stopped_df[contact_col].unique())
        print(f"Found {len(stopped_members)} members with 'Stopped' recurring status")

    # Method 2: Had membership payments before 60 days ago but not after (truly inactive)
    old_members = df_memberships[df_memberships[date_col] < sixty_days_ago][contact_col].unique()
    current_members = recent_payments[contact_col].unique()
    inactive_members = set(old_members) - set(current_members)

    # Combine both: members who cancelled OR became inactive
    quit_members = stopped_members | inactive_members
    quit_count = len(quit_members)

    # Calculate average payment per member type
    avg_payment_by_type = recent_payments.groupby('Membership Type')[amount_col].mean().to_dict() if amount_col in recent_payments.columns else {}

    # Get payment trend (last 6 months) - only memberships
    six_months_ago = now - timedelta(days=180)
    trend_data = df_memberships[df_memberships[date_col] >= six_months_ago]
    trend_data['Month'] = trend_data[date_col].dt.to_period('M')
    monthly_trend = trend_data.groupby('Month')[amount_col].sum().to_dict() if amount_col in trend_data.columns else {}
    monthly_trend = {str(k): float(v) for k, v in monthly_trend.items()}

    # Get name columns
    first_name_col = 'First Name' if 'First Name' in df.columns else None
    last_name_col = 'Last Name' if 'Last Name' in df.columns else None

    # Build detailed member lists
    active_member_list = []
    for email in current_members:
        member_data = recent_payments[recent_payments[contact_col] == email].sort_values(date_col)
        first_payment = member_data[date_col].min()
        last_payment = member_data[date_col].max()
        days_as_member = (now - first_payment).days
        membership_type = member_data['Membership Type'].iloc[-1]

        # Get recurring status
        recurring_status = 'Active'
        if recurring_col and not member_data.empty:
            recurring_status = member_data[recurring_col].iloc[-1] if not pd.isna(member_data[recurring_col].iloc[-1]) else 'Unknown'

        # Get name
        name = email
        if first_name_col and last_name_col:
            first = member_data[first_name_col].iloc[-1] if not pd.isna(member_data[first_name_col].iloc[-1]) else ''
            last = member_data[last_name_col].iloc[-1] if not pd.isna(member_data[last_name_col].iloc[-1]) else ''
            if first or last:
                name = f"{first} {last}".strip()

        active_member_list.append({
            'name': name,
            'email': email,
            'membership_type': membership_type,
            'days_as_member': int(days_as_member),
            'first_payment': first_payment.strftime('%Y-%m-%d'),
            'last_payment': last_payment.strftime('%Y-%m-%d'),
            'total_payments': len(member_data),
            'recurring_status': recurring_status
        })

    # Sort by days as member (descending)
    active_member_list.sort(key=lambda x: x['days_as_member'], reverse=True)

    # Build new member list (joined in last 30 days)
    new_member_list = []
    for member in active_member_list:
        if member['days_as_member'] <= 30:
            new_member_list.append(member)

    # Build quit member list (only those who quit in last 30 days)
    quit_member_list = []
    for email in quit_members:
        member_data = df_memberships[df_memberships[contact_col] == email].sort_values(date_col)
        last_payment = member_data[date_col].max()
        days_since_last = (now - last_payment).days

        # Only include if they quit in the last 30 days
        # (either stopped recurring recently OR last payment was 30-60 days ago)
        is_stopped = email in stopped_members

        # Skip if they're not recently quit (not stopped and last payment > 30 days ago)
        if not is_stopped and days_since_last > 30:
            continue

        membership_type = member_data['Membership Type'].iloc[-1]
        quit_reason = 'Cancelled (Recurring Stopped)' if is_stopped else 'Inactive (No recent payment)'

        # Get recurring status
        recurring_status = 'Unknown'
        if recurring_col and not member_data.empty:
            recurring_status = member_data[recurring_col].iloc[-1] if not pd.isna(member_data[recurring_col].iloc[-1]) else 'Unknown'

        # Get name
        name = email
        if first_name_col and last_name_col:
            first = member_data[first_name_col].iloc[-1] if not pd.isna(member_data[first_name_col].iloc[-1]) else ''
            last = member_data[last_name_col].iloc[-1] if not pd.isna(member_data[last_name_col].iloc[-1]) else ''
            if first or last:
                name = f"{first} {last}".strip()

        quit_member_list.append({
            'name': name,
            'email': email,
            'membership_type': membership_type,
            'last_payment': last_payment.strftime('%Y-%m-%d'),
            'days_since_last': int(days_since_last),
            'quit_reason': quit_reason,
            'recurring_status': recurring_status
        })

    # Sort quit members by days since last payment
    quit_member_list.sort(key=lambda x: x['days_since_last'])

    # Remove duplicate names and update counts
    def deduplicate_by_name(member_list):
        """Remove duplicates based on member name, keeping first occurrence"""
        seen_names = set()
        unique_list = []
        for member in member_list:
            if member['name'] not in seen_names:
                unique_list.append(member)
                seen_names.add(member['name'])
        return unique_list

    active_member_list_unique = deduplicate_by_name(active_member_list)
    new_member_list_unique = deduplicate_by_name(new_member_list)
    quit_member_list_unique = deduplicate_by_name(quit_member_list)

    # Calculate counts for ongoing vs cancelled members
    # Ongoing members = NOT stopped recurring status
    ongoing_members = [m for m in active_member_list_unique if m.get('recurring_status') != 'Stopped']
    ongoing_count = len(ongoing_members)
    total_active_count = len(active_member_list_unique)  # Includes cancelled but still active

    # Calculate projected revenue for current month in progress
    # Based on ongoing members' average monthly payment from last complete month
    if ongoing_count > 0:
        # Calculate average monthly payment from ongoing members (using last month's data)
        ongoing_emails = [m['email'] for m in ongoing_members]
        ongoing_last_month = last_month_payments[last_month_payments[contact_col].isin(ongoing_emails)]

        # If we have last month data, use it; otherwise use recent 60-day average
        if len(ongoing_last_month) > 0:
            avg_per_member = ongoing_last_month[amount_col].sum() / len(ongoing_last_month[contact_col].unique())
        else:
            ongoing_payments = recent_payments[recent_payments[contact_col].isin(ongoing_emails)]
            avg_per_member = ongoing_payments[amount_col].sum() / ongoing_count if len(ongoing_payments) > 0 else 0

        # Project current month based on ongoing members only
        projected_revenue = avg_per_member * ongoing_count
    else:
        projected_revenue = 0

    # Get month names for labels
    last_month_name = last_month_start.strftime('%B')  # e.g., "September"
    current_month_name = current_month_start.strftime('%B')  # e.g., "October"

    # Prepare dashboard data
    dashboard_data = {
        'last_updated': now.strftime('%Y-%m-%d %H:%M:%S'),
        'ongoing_members': ongoing_count,  # Active, NOT cancelled
        'total_active_members': total_active_count,  # Total including cancelled but still active
        'membership_breakdown': {k: int(v) for k, v in membership_counts.items()},
        'monthly_revenue': float(monthly_revenue),
        'monthly_revenue_month': last_month_name,  # Month name for revenue
        'projected_revenue': float(projected_revenue),
        'projected_revenue_month': current_month_name,  # Month name for projection
        'revenue_by_type': {k: float(v) for k, v in revenue_by_type.items()},
        'members_quit_60_days': len(quit_member_list_unique),  # Count unique names
        'avg_payment_by_type': {k: float(v) for k, v in avg_payment_by_type.items()},
        'monthly_trend': monthly_trend,
        'total_payments': len(df_success),
        'new_members_30_days': len(new_member_list_unique),  # Count unique names
        'active_member_list': active_member_list_unique,
        'new_member_list': new_member_list_unique,
        'quit_member_list': quit_member_list_unique
    }

    return dashboard_data

def main():
    try:
        # Get latest export file
        latest_file = get_latest_export_file()
        print(f"Processing: {latest_file}")

        # Analyze data
        data = analyze_payments(latest_file)

        # Save to JSON
        output_path = Path(OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Dashboard data generated successfully!")
        print(f"✓ Saved to: {output_path}")
        print(f"\n📊 Summary:")
        print(f"  Active Members: {data['total_active_members']}")
        print(f"  Monthly Revenue: ${data['monthly_revenue']:.2f}")
        print(f"  Members Quit (60 days): {data['members_quit_60_days']}")
        print(f"  Membership Breakdown: {data['membership_breakdown']}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
