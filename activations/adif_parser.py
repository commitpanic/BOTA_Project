"""
ADIF file parser for BOTA log imports.
Parses ADIF (.adi) files and extracts QSO data for activations.
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
from datetime import timezone as dt_timezone
from django.utils import timezone


class ADIFParser:
    """Parse ADIF format log files"""
    
    # ADIF field pattern: <FIELD:length>value or <FIELD:length:type>value
    FIELD_PATTERN = re.compile(r'<(\w+):(\d+)(?::(\w))?>([^<]*)')
    
    def __init__(self, file_content: str):
        """
        Initialize parser with file content
        
        Args:
            file_content: String content of .adi file
        """
        self.content = file_content
        self.header = {}
        self.qsos = []
    
    def parse(self) -> Dict:
        """
        Parse the ADIF file
        
        Returns:
            Dictionary with header and qsos list
        """
        # Split header and records
        parts = self.content.split('<EOH>')
        
        if len(parts) == 2:
            header_text, records_text = parts
            self.header = self._parse_fields(header_text)
        else:
            records_text = self.content
        
        # Split into individual QSO records
        qso_records = records_text.split('<EOR>')
        
        for record in qso_records:
            record = record.strip()
            if not record:
                continue
            
            qso = self._parse_fields(record)
            if qso and 'CALL' in qso:  # Valid QSO must have a callsign
                self.qsos.append(qso)
        
        return {
            'header': self.header,
            'qsos': self.qsos,
            'count': len(self.qsos)
        }
    
    def _parse_fields(self, text: str) -> Dict[str, str]:
        """
        Parse ADIF fields from text
        
        Args:
            text: Text containing ADIF fields
            
        Returns:
            Dictionary of field names to values
        """
        fields = {}
        
        for match in self.FIELD_PATTERN.finditer(text):
            field_name = match.group(1).upper()
            field_length = int(match.group(2))
            # field_type = match.group(3)  # Optional type indicator
            field_value = match.group(4)[:field_length]  # Ensure correct length
            
            fields[field_name] = field_value.strip()
        
        return fields
    
    def extract_bunker_reference(self) -> Optional[str]:
        """
        Extract bunker reference from QSO records
        Looks for MY_SIG_INFO field containing bunker ID (e.g., B/SP-0039)
        
        Returns:
            Bunker reference string or None
        """
        for qso in self.qsos:
            if 'MY_SIG_INFO' in qso:
                bunker_ref = qso['MY_SIG_INFO'].strip()
                # Validate format: B/XX-#### (e.g., B/SP-0039)
                if re.match(r'^B/[A-Z]{2}-\d{4}$', bunker_ref):
                    return bunker_ref
        
        return None
    
    def extract_activator_callsign(self) -> Optional[str]:
        """
        Extract activator callsign from header or QSO records
        Looks for OPERATOR or STATION_CALLSIGN fields
        
        Returns:
            Activator callsign or None
        """
        # Try header first
        if 'OPERATOR' in self.header:
            return self.header['OPERATOR'].strip().upper()
        if 'STATION_CALLSIGN' in self.header:
            return self.header['STATION_CALLSIGN'].strip().upper()
        
        # Try first QSO record
        if self.qsos:
            first_qso = self.qsos[0]
            if 'OPERATOR' in first_qso:
                return first_qso['OPERATOR'].strip().upper()
            if 'STATION_CALLSIGN' in first_qso:
                return first_qso['STATION_CALLSIGN'].strip().upper()
        
        return None
    
    def parse_qso_datetime(self, qso: Dict) -> Optional[datetime]:
        """
        Parse QSO date and time into datetime object
        
        Args:
            qso: QSO record dictionary
            
        Returns:
            datetime object or None
        """
        if 'QSO_DATE' not in qso or 'TIME_ON' not in qso:
            return None
        
        try:
            # QSO_DATE format: YYYYMMDD
            # TIME_ON format: HHMMSS or HHMM
            date_str = qso['QSO_DATE']
            time_str = qso['TIME_ON']
            
            # Pad time to 6 digits if needed
            time_str = time_str.ljust(6, '0')
            
            # Parse datetime
            dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            
            # Make timezone aware (assume UTC for ham radio logs)
            return timezone.make_aware(dt, dt_timezone.utc)
        
        except (ValueError, KeyError):
            return None
    
    def extract_hunter_callsigns(self) -> List[str]:
        """
        Extract list of unique hunter callsigns from all QSOs
        
        Returns:
            List of hunter callsigns
        """
        callsigns = set()
        
        for qso in self.qsos:
            if 'CALL' in qso:
                callsign = qso['CALL'].strip().upper()
                if callsign:
                    callsigns.add(callsign)
        
        return sorted(list(callsigns))
    
    def is_b2b_qso(self, qso: Dict) -> bool:
        """
        Check if QSO is bunker-to-bunker (B2B)
        Looks for SIG and SIG_INFO fields indicating other station is also at a bunker
        
        Args:
            qso: QSO record dictionary
            
        Returns:
            True if B2B QSO, False otherwise
        """
        # Check if other station has SIG=WWBOTA and SIG_INFO with bunker reference
        if 'SIG' in qso and qso['SIG'].upper() == 'WWBOTA':
            if 'SIG_INFO' in qso:
                sig_info = qso['SIG_INFO'].strip()
                # Check for bunker reference format
                if re.match(r'^B/[A-Z]{2}-\d{4}$', sig_info):
                    return True
        
        return False
    
    def get_qso_mode(self, qso: Dict) -> str:
        """
        Extract QSO mode (e.g., SSB, CW, FM, FT8)
        
        Args:
            qso: QSO record dictionary
            
        Returns:
            Mode string or 'UNKNOWN'
        """
        return qso.get('MODE', 'UNKNOWN').upper()
    
    def get_qso_band(self, qso: Dict) -> str:
        """
        Extract QSO band (e.g., 80m, 40m, 2m)
        
        Args:
            qso: QSO record dictionary
            
        Returns:
            Band string or 'UNKNOWN'
        """
        return qso.get('BAND', 'UNKNOWN').upper()
    
    def validate(self) -> Dict[str, any]:
        """
        Validate parsed ADIF data for BOTA requirements
        
        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Check for bunker reference
        bunker_ref = self.extract_bunker_reference()
        if not bunker_ref:
            errors.append("No valid bunker reference found (MY_SIG_INFO field)")
        
        # Check for activator callsign
        activator = self.extract_activator_callsign()
        if not activator:
            errors.append("No activator callsign found (OPERATOR or STATION_CALLSIGN field)")
        
        # Check for QSOs
        if not self.qsos:
            errors.append("No QSO records found in file")
        
        # Validate each QSO has required fields
        for i, qso in enumerate(self.qsos):
            if 'CALL' not in qso:
                errors.append(f"QSO {i+1}: Missing CALL field")
            if 'QSO_DATE' not in qso:
                errors.append(f"QSO {i+1}: Missing QSO_DATE field")
            if 'TIME_ON' not in qso:
                errors.append(f"QSO {i+1}: Missing TIME_ON field")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': []
        }


def parse_adif_file(file_content: str) -> Dict:
    """
    Convenience function to parse ADIF file
    
    Args:
        file_content: String content of .adi file
        
    Returns:
        Parsed data dictionary
    """
    parser = ADIFParser(file_content)
    data = parser.parse()
    validation = parser.validate()
    
    return {
        'header': data['header'],
        'qsos': data['qsos'],
        'count': data['count'],
        'bunker_reference': parser.extract_bunker_reference(),
        'activator_callsign': parser.extract_activator_callsign(),
        'hunter_callsigns': parser.extract_hunter_callsigns(),
        'validation': validation
    }
