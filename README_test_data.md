# DMARC Test Data Generator

This script generates realistic DMARC XML reports for testing and development purposes.

## Features

- **5 Separate XML Reports** distributed across different days
- **~10,000 Total Emails** distributed realistically across reports
- **Legitimate Third-Party Senders** including:
  - Mailchimp
  - SendGrid
  - Amazon SES
  - Google Workspace
  - Microsoft Outlook
  - Constant Contact
  - HubSpot
- **Realistic Authentication Rates** (~20% overall pass rate)
- **Suspicious/Malicious Senders** with low authentication rates
- **Compressed Output** (gzip) for realistic file sizes

## Usage

### Basic Usage
```bash
# Generate test reports for example.com
python generate_test_dmarc_reports.py

# Generate for your domain
python generate_test_dmarc_reports.py --domain your-domain.com

# Custom email volume
python generate_test_dmarc_reports.py --total-emails 15000 --num-reports 7

# Uncompressed XML files
python generate_test_dmarc_reports.py --no-compress
```

### Command Line Options
- `--domain`: Domain name for reports (default: example.com)
- `--total-emails`: Total emails across all reports (default: 10000)
- `--num-reports`: Number of separate reports (default: 5)
- `--no-compress`: Save as plain XML instead of gzip compressed

## Output

The script creates a `test_dmarc_reports/` directory containing:

- **XML Report Files**: `test_report_N_XXXXXX.xml.gz`
- **Summary File**: `test_data_summary.txt` with statistics

## Test Data Characteristics

### Legitimate Senders (80% of volume)
- **Mailchimp**: 20% of emails, 95% authentication rate
- **SendGrid**: 15% of emails, 90% authentication rate  
- **Amazon SES**: 12% of emails, 88% authentication rate
- **Google**: 18% of emails, 92% authentication rate
- **Outlook**: 10% of emails, 85% authentication rate
- **Constant Contact**: 8% of emails, 82% authentication rate
- **HubSpot**: 7% of emails, 87% authentication rate

### Suspicious Senders (10% of volume)
- **phishing-attempt.tk**: 3% of emails, 2% authentication rate
- **suspicious-domain.ru**: 2% of emails, 5% authentication rate
- **fake-bank-alerts.ml**: 2% of emails, 1% authentication rate
- **spoofed-company.ga**: 3% of emails, 3% authentication rate

## Integration with DMARC App

To test the generated reports in your DMARC application:

1. **Generate the reports**:
   ```bash
   python generate_test_dmarc_reports.py --domain your-test-domain.com
   ```

2. **Upload via the web interface**:
   - Go to the "Upload" tab in your DMARC app
   - Drag and drop the generated `.xml.gz` files
   - The app will process and display the data

3. **Expected results**:
   - Dashboard will show mixed authentication results
   - Alerts may be triggered for suspicious senders
   - DNS records page can analyze the test domain
   - Charts will display realistic email volume patterns

## Customization

The script can be easily modified to:
- Add more third-party email services
- Adjust authentication rates
- Include different types of suspicious activity
- Change email volume distributions
- Add custom IP ranges or domains

## Technical Details

- **XML Format**: Standard DMARC aggregate report format (RFC 7489)
- **IP Generation**: Realistic IP addresses from actual service provider ranges
- **Authentication Logic**: Proper SPF/DKIM result simulation
- **Date Ranges**: Reports span multiple days for realistic testing
- **Compression**: gzip compression matching real-world report delivery