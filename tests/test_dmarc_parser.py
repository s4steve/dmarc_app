"""
Tests for DMARC XML parsing functionality
"""
import pytest
from datetime import datetime
from backend.app.services.dmarc_parser import DMARCParser

class TestDMARCParser:
    """Test DMARC XML parsing functionality"""
    
    def setup_method(self):
        self.parser = DMARCParser()
    
    def test_parse_valid_xml_report(self, sample_dmarc_xml):
        """Test parsing of valid DMARC XML report"""
        report = self.parser.parse_xml_report(sample_dmarc_xml, "test_customer")
        
        assert report.customer_id == "test_customer"
        assert report.metadata.org_name == "Test Organization"
        assert report.metadata.email == "test@example.com"
        assert report.metadata.report_id == "test_report_123"
        assert report.policy.domain == "example.com"
        assert report.policy.p == "none"
        assert len(report.records) == 2
        
        # Test first record (passing)
        record1 = report.records[0]
        assert record1.source_ip == "192.168.1.1"
        assert record1.count == 100
        assert record1.spf_result == "pass"
        assert record1.dkim_result == "pass"
        assert record1.dmarc_result == "pass"  # Should be pass since both SPF and DKIM pass
        
        # Test second record (failing)
        record2 = report.records[1]
        assert record2.source_ip == "10.0.0.1"
        assert record2.count == 50
        assert record2.spf_result == "fail"
        assert record2.dkim_result == "fail"
        assert record2.dmarc_result == "fail"  # Should be fail since both SPF and DKIM fail
    
    def test_dmarc_result_determination(self):
        """Test DMARC pass/fail logic - REGRESSION TEST for issue we fixed"""
        # Test both pass
        assert self.parser._determine_dmarc_result("pass", "pass") == "pass"
        
        # Test SPF pass, DKIM fail - should still pass
        assert self.parser._determine_dmarc_result("pass", "fail") == "pass"
        
        # Test SPF fail, DKIM pass - should still pass  
        assert self.parser._determine_dmarc_result("fail", "pass") == "pass"
        
        # Test both fail
        assert self.parser._determine_dmarc_result("fail", "fail") == "fail"
        
        # Test other values
        assert self.parser._determine_dmarc_result("none", "pass") == "pass"
        assert self.parser._determine_dmarc_result("none", "none") == "fail"
    
    def test_parse_malformed_xml(self):
        """Test parsing of malformed XML"""
        malformed_xml = "<invalid><unclosed>xml</invalid>"
        
        with pytest.raises(ValueError, match="Failed to parse DMARC report"):
            self.parser.parse_xml_report(malformed_xml, "test_customer")
    
    def test_parse_empty_xml(self):
        """Test parsing of empty XML"""
        with pytest.raises(ValueError):
            self.parser.parse_xml_report("", "test_customer")
    
    def test_parse_xml_missing_records(self):
        """Test parsing XML with missing records section"""
        xml_no_records = """<?xml version="1.0" encoding="UTF-8"?>
        <feedback>
            <report_metadata>
                <org_name>Test</org_name>
                <email>test@example.com</email>
                <report_id>test</report_id>
                <date_range>
                    <begin>1640995200</begin>
                    <end>1641081600</end>
                </date_range>
            </report_metadata>
            <policy_published>
                <domain>example.com</domain>
                <p>none</p>
            </policy_published>
        </feedback>"""
        
        report = self.parser.parse_xml_report(xml_no_records, "test_customer")
        assert len(report.records) == 0
    
    def test_parse_xml_single_record(self):
        """Test parsing XML with single record (not in array)"""
        xml_single_record = """<?xml version="1.0" encoding="UTF-8"?>
        <feedback>
            <report_metadata>
                <org_name>Test</org_name>
                <email>test@example.com</email>
                <report_id>test</report_id>
                <date_range>
                    <begin>1640995200</begin>
                    <end>1641081600</end>
                </date_range>
            </report_metadata>
            <policy_published>
                <domain>example.com</domain>
                <p>none</p>
            </policy_published>
            <record>
                <row>
                    <source_ip>1.2.3.4</source_ip>
                    <count>10</count>
                </row>
                <identifiers>
                    <header_from>example.com</header_from>
                </identifiers>
                <auth_results>
                    <spf><result>pass</result></spf>
                    <dkim><result>fail</result></dkim>
                </auth_results>
            </record>
        </feedback>"""
        
        report = self.parser.parse_xml_report(xml_single_record, "test_customer")
        assert len(report.records) == 1
        assert report.records[0].source_ip == "1.2.3.4"
        assert report.records[0].dmarc_result == "pass"  # SPF passes, so DMARC passes