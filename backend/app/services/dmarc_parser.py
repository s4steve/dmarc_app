import xmltodict
import json
from typing import Dict, Any, List
from datetime import datetime
from ..models.dmarc import DMARCReport, DMARCReportMetadata, DMARCReportPolicy, DMARCRecord

class DMARCParser:
    def parse_xml_report(self, xml_content: str, customer_id: str) -> DMARCReport:
        try:
            data = xmltodict.parse(xml_content)
            feedback = data.get('feedback', {})
            
            metadata = self._parse_metadata(feedback.get('report_metadata', {}))
            policy = self._parse_policy(feedback.get('policy_published', {}))
            records = self._parse_records(feedback.get('record', []))
            
            return DMARCReport(
                customer_id=customer_id,
                metadata=metadata,
                policy=policy,
                records=records,
                processed_at=datetime.utcnow(),
                raw_xml=xml_content
            )
        except Exception as e:
            raise ValueError(f"Failed to parse DMARC report: {str(e)}")
    
    def _parse_metadata(self, metadata: Dict[str, Any]) -> DMARCReportMetadata:
        date_range = metadata.get('date_range', {})
        
        return DMARCReportMetadata(
            org_name=metadata.get('org_name', ''),
            email=metadata.get('email', ''),
            report_id=metadata.get('report_id', ''),
            date_range_begin=datetime.fromtimestamp(int(date_range.get('begin', 0))),
            date_range_end=datetime.fromtimestamp(int(date_range.get('end', 0)))
        )
    
    def _parse_policy(self, policy: Dict[str, Any]) -> DMARCReportPolicy:
        return DMARCReportPolicy(
            domain=policy.get('domain', ''),
            adkim=policy.get('adkim'),
            aspf=policy.get('aspf'),
            p=policy.get('p', ''),
            sp=policy.get('sp'),
            pct=int(policy.get('pct', 100))
        )
    
    def _parse_records(self, records_data: Any) -> List[DMARCRecord]:
        records = []
        
        if not isinstance(records_data, list):
            records_data = [records_data] if records_data else []
        
        for record_data in records_data:
            row = record_data.get('row', {})
            identifiers = record_data.get('identifiers', {})
            auth_results = record_data.get('auth_results', {})
            
            spf_results = auth_results.get('spf', [])
            dkim_results = auth_results.get('dkim', [])
            
            if not isinstance(spf_results, list):
                spf_results = [spf_results] if spf_results else []
            if not isinstance(dkim_results, list):
                dkim_results = [dkim_results] if dkim_results else []
            
            spf_result = spf_results[0].get('result', 'none') if spf_results else 'none'
            dkim_result = dkim_results[0].get('result', 'none') if dkim_results else 'none'
            
            record = DMARCRecord(
                source_ip=row.get('source_ip', ''),
                count=int(row.get('count', 0)),
                spf_result=spf_result,
                dkim_result=dkim_result,
                dmarc_result=self._determine_dmarc_result(spf_result, dkim_result),
                header_from=identifiers.get('header_from', ''),
                envelope_from=identifiers.get('envelope_from', '')
            )
            records.append(record)
        
        return records
    
    def _determine_dmarc_result(self, spf_result: str, dkim_result: str) -> str:
        """
        Determine DMARC result based on SPF and DKIM results.
        DMARC passes if either SPF or DKIM passes (or both).
        """
        if spf_result == 'pass' or dkim_result == 'pass':
            return 'pass'
        else:
            return 'fail'

dmarc_parser = DMARCParser()