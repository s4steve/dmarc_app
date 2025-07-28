#!/usr/bin/env python3
"""
DMARC Test Report Generator

Generates realistic DMARC XML reports for testing purposes.
Creates 5 separate XML reports with approximately 10,000 total emails,
including legitimate third-party senders, authentication failures, and suspicious activity.
"""

import xml.etree.ElementTree as ET
import random
import datetime
import gzip
from pathlib import Path
from typing import List, Dict, Tuple
import argparse

class DMARCReportGenerator:
    def __init__(self, domain: str = "example.com"):
        self.domain = domain
        self.output_dir = Path("test_dmarc_reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # Well-known third-party email service providers
        self.legitimate_senders = {
            "mailchimp.com": {
                "ips": ["198.2.128.0/24", "198.2.129.0/24", "205.201.128.0/24"],
                "spf_domain": "servers.mcsv.net",
                "dkim_selector": "k1",
                "auth_rate": 0.95,
                "volume_weight": 0.20
            },
            "sendgrid.net": {
                "ips": ["149.72.0.0/16", "208.115.214.0/24", "167.89.0.0/16"],
                "spf_domain": "sendgrid.net",
                "dkim_selector": "s1",
                "auth_rate": 0.90,
                "volume_weight": 0.15
            },
            "amazonses.com": {
                "ips": ["54.240.0.0/18", "69.169.224.0/20", "23.249.208.0/20"],
                "spf_domain": "amazonses.com",
                "dkim_selector": "7v7vs6w47njt4pimodk5mmttbegzsi6n",
                "auth_rate": 0.88,
                "volume_weight": 0.12
            },
            "google.com": {
                "ips": ["209.85.128.0/17", "64.233.160.0/19", "66.249.80.0/20"],
                "spf_domain": "_spf.google.com",
                "dkim_selector": "20161025",
                "auth_rate": 0.92,
                "volume_weight": 0.18
            },
            "outlook.com": {
                "ips": ["40.92.0.0/15", "40.107.0.0/16", "52.100.0.0/14"],
                "spf_domain": "spf.protection.outlook.com",
                "dkim_selector": "selector1",
                "auth_rate": 0.85,
                "volume_weight": 0.10
            },
            "constantcontact.com": {
                "ips": ["208.75.122.0/24", "208.75.123.0/24", "69.46.64.0/18"],
                "spf_domain": "spf.constantcontact.com",
                "dkim_selector": "1000073432",
                "auth_rate": 0.82,
                "volume_weight": 0.08
            },
            "hubspot.com": {
                "ips": ["198.21.0.0/21", "198.2.180.0/24", "104.196.0.0/14"],
                "spf_domain": "_spf.hubspotemail.net",
                "dkim_selector": "hs1",
                "auth_rate": 0.87,
                "volume_weight": 0.07
            }
        }
        
        # Suspicious/potentially malicious senders
        self.suspicious_senders = {
            "phishing-attempt.tk": {
                "ips": ["185.220.100.240", "185.220.101.19", "185.220.102.8"],
                "auth_rate": 0.02,
                "volume_weight": 0.03
            },
            "suspicious-domain.ru": {
                "ips": ["91.218.67.115", "91.218.67.116", "91.218.67.117"],
                "auth_rate": 0.05,
                "volume_weight": 0.02
            },
            "fake-bank-alerts.ml": {
                "ips": ["103.224.182.245", "103.224.182.246", "103.224.182.247"],
                "auth_rate": 0.01,
                "volume_weight": 0.02
            },
            "spoofed-company.ga": {
                "ips": ["176.123.26.71", "176.123.26.72", "176.123.26.73"],
                "auth_rate": 0.03,
                "volume_weight": 0.03
            }
        }

    def generate_ip_from_cidr(self, cidr: str) -> str:
        """Generate a random IP address from a CIDR block."""
        if '/' not in cidr:
            return cidr
        
        network, prefix = cidr.split('/')
        prefix = int(prefix)
        
        # Convert network to integer
        parts = network.split('.')
        network_int = (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
        
        # Calculate range
        host_bits = 32 - prefix
        max_hosts = (1 << host_bits) - 1
        
        # Generate random host
        random_host = random.randint(1, max_hosts)
        ip_int = network_int + random_host
        
        # Convert back to IP
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"

    def generate_record(self, sender_info: Dict, sender_domain: str, is_suspicious: bool = False) -> Dict:
        """Generate a single DMARC record."""
        # Randomly select an IP from the sender's pool
        ip_pool = sender_info["ips"]
        source_ip = self.generate_ip_from_cidr(random.choice(ip_pool))
        
        # Determine authentication results based on sender's auth rate
        auth_rate = sender_info["auth_rate"]
        spf_pass = random.random() < auth_rate
        dkim_pass = random.random() < auth_rate
        
        # Generate email count (realistic distribution)
        if is_suspicious:
            count = random.randint(1, 10)  # Suspicious senders typically have lower volume
        else:
            # Use weighted random for legitimate senders
            weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # Favor smaller batches
            ranges = [(1, 50), (51, 200), (201, 500), (501, 1000), (1001, 2000)]
            count_range = random.choices(ranges, weights=weights)[0]
            count = random.randint(*count_range)
        
        record = {
            "source_ip": source_ip,
            "count": count,
            "disposition": random.choice(["none", "quarantine", "reject"]) if not spf_pass and not dkim_pass else "none",
            "dkim_domain": self.domain,
            "dkim_result": "pass" if dkim_pass else "fail",
            "dkim_selector": sender_info.get("dkim_selector", "default"),
            "spf_domain": self.domain,
            "spf_result": "pass" if spf_pass else "fail",
            "envelope_from": f"bounce@{sender_domain}",
            "header_from": self.domain,
            "envelope_to": f"user@{self.domain}"
        }
        
        return record

    def create_report_xml(self, report_id: str, date_range: Tuple[datetime.datetime, datetime.datetime], 
                         records: List[Dict]) -> str:
        """Create XML report structure."""
        start_date, end_date = date_range
        
        # Root element
        feedback = ET.Element("feedback")
        
        # Report metadata
        report_metadata = ET.SubElement(feedback, "report_metadata")
        ET.SubElement(report_metadata, "org_name").text = "DMARC Report Generator"
        ET.SubElement(report_metadata, "email").text = "noreply@dmarcanalyzer.com"
        ET.SubElement(report_metadata, "extra_contact_info").text = "Test report generated for development"
        ET.SubElement(report_metadata, "report_id").text = report_id
        
        date_range_elem = ET.SubElement(report_metadata, "date_range")
        ET.SubElement(date_range_elem, "begin").text = str(int(start_date.timestamp()))
        ET.SubElement(date_range_elem, "end").text = str(int(end_date.timestamp()))
        
        # Policy published
        policy_published = ET.SubElement(feedback, "policy_published")
        ET.SubElement(policy_published, "domain").text = self.domain
        ET.SubElement(policy_published, "adkim").text = "r"  # relaxed
        ET.SubElement(policy_published, "aspf").text = "r"   # relaxed
        ET.SubElement(policy_published, "p").text = "none"   # policy
        ET.SubElement(policy_published, "sp").text = "none"  # subdomain policy
        ET.SubElement(policy_published, "pct").text = "100"  # percentage
        
        # Records
        for record_data in records:
            record = ET.SubElement(feedback, "record")
            
            # Row
            row = ET.SubElement(record, "row")
            ET.SubElement(row, "source_ip").text = record_data["source_ip"]
            ET.SubElement(row, "count").text = str(record_data["count"])
            
            policy_evaluated = ET.SubElement(row, "policy_evaluated")
            ET.SubElement(policy_evaluated, "disposition").text = record_data["disposition"]
            ET.SubElement(policy_evaluated, "dkim").text = record_data["dkim_result"]
            ET.SubElement(policy_evaluated, "spf").text = record_data["spf_result"]
            
            # Identifiers
            identifiers = ET.SubElement(record, "identifiers")
            ET.SubElement(identifiers, "envelope_to").text = record_data["envelope_to"]
            ET.SubElement(identifiers, "header_from").text = record_data["header_from"]
            ET.SubElement(identifiers, "envelope_from").text = record_data["envelope_from"]
            
            # Auth results
            auth_results = ET.SubElement(record, "auth_results")
            
            # DKIM
            dkim = ET.SubElement(auth_results, "dkim")
            ET.SubElement(dkim, "domain").text = record_data["dkim_domain"]
            ET.SubElement(dkim, "selector").text = record_data["dkim_selector"]
            ET.SubElement(dkim, "result").text = record_data["dkim_result"]
            
            # SPF
            spf = ET.SubElement(auth_results, "spf")
            ET.SubElement(spf, "domain").text = record_data["spf_domain"]
            ET.SubElement(spf, "scope").text = "mfrom"
            ET.SubElement(spf, "result").text = record_data["spf_result"]
        
        return ET.tostring(feedback, encoding='unicode', xml_declaration=True)

    def generate_reports(self, total_emails: int = 10000, num_reports: int = 5) -> List[str]:
        """Generate multiple DMARC reports."""
        reports = []
        emails_per_report = total_emails // num_reports
        
        for i in range(num_reports):
            report_id = f"test_report_{i+1}_{random.randint(100000, 999999)}"
            
            # Generate date range (reports from different days)
            base_date = datetime.datetime.now() - datetime.timedelta(days=7-i)
            start_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + datetime.timedelta(days=1)
            
            records = []
            current_email_count = 0
            
            # Distribute emails among legitimate senders
            for sender_domain, sender_info in self.legitimate_senders.items():
                target_count = int(emails_per_report * sender_info["volume_weight"])
                
                while current_email_count < target_count:
                    record = self.generate_record(sender_info, sender_domain)
                    records.append(record)
                    current_email_count += record["count"]
                    
                    if current_email_count >= target_count:
                        break
            
            # Add suspicious senders
            for sender_domain, sender_info in self.suspicious_senders.items():
                if random.random() < 0.7:  # 70% chance to include each suspicious sender
                    target_count = int(emails_per_report * sender_info["volume_weight"])
                    suspicious_count = 0
                    
                    while suspicious_count < target_count:
                        record = self.generate_record(sender_info, sender_domain, is_suspicious=True)
                        records.append(record)
                        suspicious_count += record["count"]
                        current_email_count += record["count"]
                        
                        if suspicious_count >= target_count:
                            break
            
            # Fill remaining quota with additional legitimate traffic
            remaining = emails_per_report - current_email_count
            if remaining > 0:
                sender_domain = random.choice(list(self.legitimate_senders.keys()))
                sender_info = self.legitimate_senders[sender_domain]
                while current_email_count < emails_per_report:
                    record = self.generate_record(sender_info, sender_domain)
                    records.append(record)
                    current_email_count += record["count"]
                    
                    if current_email_count >= emails_per_report:
                        break
            
            # Create XML report
            xml_content = self.create_report_xml(report_id, (start_date, end_date), records)
            reports.append((report_id, xml_content, current_email_count))
            
            print(f"Generated report {i+1}/{num_reports}: {report_id} ({current_email_count} emails, {len(records)} records)")
        
        return reports

    def save_reports(self, reports: List[Tuple[str, str, int]], compress: bool = True):
        """Save reports to files."""
        total_emails = sum(count for _, _, count in reports)
        
        for report_id, xml_content, email_count in reports:
            if compress:
                filename = f"{report_id}.xml.gz"
                filepath = self.output_dir / filename
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(xml_content)
            else:
                filename = f"{report_id}.xml"
                filepath = self.output_dir / filename
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
            
            print(f"Saved: {filename} ({email_count} emails)")
        
        print(f"\nGeneration complete!")
        print(f"Total reports: {len(reports)}")
        print(f"Total emails: {total_emails:,}")
        print(f"Output directory: {self.output_dir.absolute()}")
        
        # Generate summary
        self.generate_summary(reports)

    def generate_summary(self, reports: List[Tuple[str, str, int]]):
        """Generate a summary of the test data."""
        summary_file = self.output_dir / "test_data_summary.txt"
        
        total_emails = sum(count for _, _, count in reports)
        
        with open(summary_file, 'w') as f:
            f.write("DMARC Test Data Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Domain: {self.domain}\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Reports: {len(reports)}\n")
            f.write(f"Total Emails: {total_emails:,}\n\n")
            
            f.write("Legitimate Email Service Providers:\n")
            f.write("-" * 40 + "\n")
            for domain, info in self.legitimate_senders.items():
                expected_volume = int(total_emails * info["volume_weight"])
                f.write(f"  {domain:<25} ~{expected_volume:>6,} emails ({info['auth_rate']*100:.0f}% auth rate)\n")
            
            f.write("\nSuspicious/Malicious Senders:\n")
            f.write("-" * 40 + "\n")
            for domain, info in self.suspicious_senders.items():
                expected_volume = int(total_emails * info["volume_weight"])
                f.write(f"  {domain:<25} ~{expected_volume:>6,} emails ({info['auth_rate']*100:.0f}% auth rate)\n")
            
            f.write(f"\nExpected Authentication Statistics:\n")
            f.write("-" * 40 + "\n")
            
            # Calculate expected pass rate
            total_weight = sum(info["volume_weight"] * info["auth_rate"] for info in self.legitimate_senders.values())
            total_weight += sum(info["volume_weight"] * info["auth_rate"] for info in self.suspicious_senders.values())
            
            expected_pass_rate = total_weight * 100
            f.write(f"  Expected overall authentication pass rate: ~{expected_pass_rate:.1f}%\n")
            f.write(f"  Expected authentication failure rate: ~{100-expected_pass_rate:.1f}%\n\n")
            
            f.write("Files Generated:\n")
            f.write("-" * 40 + "\n")
            for report_id, _, email_count in reports:
                f.write(f"  {report_id}.xml.gz ({email_count:,} emails)\n")
        
        print(f"Summary saved: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate test DMARC XML reports")
    parser.add_argument("--domain", default="example.com", help="Domain for DMARC reports (default: example.com)")
    parser.add_argument("--total-emails", type=int, default=10000, help="Total number of emails across all reports (default: 10000)")
    parser.add_argument("--num-reports", type=int, default=5, help="Number of reports to generate (default: 5)")
    parser.add_argument("--no-compress", action="store_true", help="Don't compress XML files with gzip")
    
    args = parser.parse_args()
    
    print(f"Generating DMARC test reports for domain: {args.domain}")
    print(f"Target total emails: {args.total_emails:,}")
    print(f"Number of reports: {args.num_reports}")
    print("-" * 50)
    
    generator = DMARCReportGenerator(domain=args.domain)
    reports = generator.generate_reports(total_emails=args.total_emails, num_reports=args.num_reports)
    generator.save_reports(reports, compress=not args.no_compress)

if __name__ == "__main__":
    main()