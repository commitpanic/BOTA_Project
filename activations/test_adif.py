"""
Tests for ADIF parser and log import service.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from activations.adif_parser import ADIFParser, parse_adif_file
from activations.log_import_service import LogImportService
from bunkers.models import Bunker, BunkerCategory

User = get_user_model()


class ADIFParserTest(TestCase):
    """Test ADIF parser functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.sample_adif = """ADIF for SP3FCK: WWBOTA at B/SP-0039 K705 on 2025-11-04 
<ADIF_VER:5>3.1.5
<PROGRAMID:21>Ham2K Portable Logger
<PROGRAMVERSION:6>25.9.3
Stations Worked: 6
B2B QSOs: 0

<EOH>
<CALL:6>SP3BLZ <MODE:3>SSB <BAND:3>80m <FREQ:8>3.710000 <QSO_DATE:8>20251104 <TIME_ON:6>201514 <RST_RCVD:2>59 <RST_SENT:2>59 <STATION_CALLSIGN:6>SP3FCK <OPERATOR:6>SP3FCK <DXCC:3>269 <STATE:2>PL <CQZ:2>15 <ITUZ:2>28 <QSLMSG:12>SP B/SP-0039 <MY_SIG:6>WWBOTA <MY_SIG_INFO:9>B/SP-0039 <EOR>
<CALL:6>SQ3BMJ <MODE:3>SSB <BAND:3>80m <FREQ:8>3.710000 <QSO_DATE:8>20251104 <TIME_ON:6>201523 <RST_RCVD:2>59 <RST_SENT:2>59 <STATION_CALLSIGN:6>SP3FCK <OPERATOR:6>SP3FCK <DXCC:3>269 <CQZ:2>15 <ITUZ:2>28 <QSLMSG:12>SP B/SP-0039 <MY_SIG:6>WWBOTA <MY_SIG_INFO:9>B/SP-0039 <EOR>
<CALL:6>SP3BKR <MODE:3>SSB <BAND:3>80m <FREQ:8>3.710000 <QSO_DATE:8>20251104 <TIME_ON:6>201533 <RST_RCVD:2>59 <RST_SENT:2>59 <STATION_CALLSIGN:6>SP3FCK <OPERATOR:6>SP3FCK <DXCC:3>269 <CQZ:2>15 <ITUZ:2>28 <QSLMSG:12>SP B/SP-0039 <MY_SIG:6>WWBOTA <MY_SIG_INFO:9>B/SP-0039 <EOR>
"""
    
    def test_parse_header(self):
        """Test parsing ADIF header"""
        parser = ADIFParser(self.sample_adif)
        result = parser.parse()
        
        self.assertIn('header', result)
        self.assertEqual(result['header']['ADIF_VER'], '3.1.5')
        self.assertEqual(result['header']['PROGRAMID'], 'Ham2K Portable Logger')
    
    def test_parse_qsos(self):
        """Test parsing QSO records"""
        parser = ADIFParser(self.sample_adif)
        result = parser.parse()
        
        self.assertEqual(result['count'], 3)
        self.assertEqual(len(result['qsos']), 3)
        
        # Check first QSO
        first_qso = result['qsos'][0]
        self.assertEqual(first_qso['CALL'], 'SP3BLZ')
        self.assertEqual(first_qso['MODE'], 'SSB')
        self.assertEqual(first_qso['BAND'], '80m')
        self.assertEqual(first_qso['MY_SIG_INFO'], 'B/SP-0039')
    
    def test_extract_bunker_reference(self):
        """Test extracting bunker reference"""
        parser = ADIFParser(self.sample_adif)
        parser.parse()
        
        bunker_ref = parser.extract_bunker_reference()
        self.assertEqual(bunker_ref, 'B/SP-0039')
    
    def test_extract_activator_callsign(self):
        """Test extracting activator callsign"""
        parser = ADIFParser(self.sample_adif)
        parser.parse()
        
        activator = parser.extract_activator_callsign()
        self.assertEqual(activator, 'SP3FCK')
    
    def test_extract_hunter_callsigns(self):
        """Test extracting hunter callsigns"""
        parser = ADIFParser(self.sample_adif)
        parser.parse()
        
        hunters = parser.extract_hunter_callsigns()
        self.assertEqual(len(hunters), 3)
        self.assertIn('SP3BLZ', hunters)
        self.assertIn('SQ3BMJ', hunters)
        self.assertIn('SP3BKR', hunters)
    
    def test_validation(self):
        """Test ADIF validation"""
        parser = ADIFParser(self.sample_adif)
        parser.parse()
        
        validation = parser.validate()
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
    
    def test_parse_qso_datetime(self):
        """Test parsing QSO date/time"""
        parser = ADIFParser(self.sample_adif)
        result = parser.parse()
        
        qso = result['qsos'][0]
        dt = parser.parse_qso_datetime(qso)
        
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2025)
        self.assertEqual(dt.month, 11)
        self.assertEqual(dt.day, 4)
        self.assertEqual(dt.hour, 20)
        self.assertEqual(dt.minute, 15)


class LogImportServiceTest(TestCase):
    """Test log import service"""
    
    def setUp(self):
        """Set up test data"""
        # Create category
        self.category = BunkerCategory.objects.create(
            name_pl='Schron',
            name_en='Shelter'
        )
        
        # Create bunker
        self.bunker = Bunker.objects.create(
            reference_number='B/SP-0039',
            name_pl='K705',
            name_en='K705',
            category=self.category,
            latitude=Decimal('52.0'),
            longitude=Decimal('21.0')
        )
        
        # Create activator user
        self.activator = User.objects.create_user(
            email='sp3fck@test.com',
            callsign='SP3FCK',
            password='testpass123'
        )
        
        # Sample ADIF content
        self.sample_adif = """<ADIF_VER:5>3.1.5
<EOH>
<CALL:6>SP3BLZ <MODE:3>SSB <BAND:3>80m <QSO_DATE:8>20251104 <TIME_ON:6>201514 <STATION_CALLSIGN:6>SP3FCK <OPERATOR:6>SP3FCK <MY_SIG:6>WWBOTA <MY_SIG_INFO:9>B/SP-0039 <EOR>
<CALL:6>SQ3BMJ <MODE:3>SSB <BAND:3>80m <QSO_DATE:8>20251104 <TIME_ON:6>201523 <STATION_CALLSIGN:6>SP3FCK <OPERATOR:6>SP3FCK <MY_SIG:6>WWBOTA <MY_SIG_INFO:9>B/SP-0039 <EOR>
"""
    
    def test_process_adif_upload(self):
        """Test processing ADIF upload"""
        service = LogImportService()
        result = service.process_adif_upload(self.sample_adif, self.activator)
        
        # Print warnings if any
        if result.get('warnings'):
            print(f"\nWarnings: {result['warnings']}")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['qsos_processed'], 2)
        self.assertEqual(result['hunters_updated'], 2)
        self.assertEqual(result['bunker'], 'B/SP-0039')
        self.assertEqual(result['activator'], 'SP3FCK')
    
    def test_hunter_points_awarded(self):
        """Test that hunter points are awarded"""
        service = LogImportService()
        service.process_adif_upload(self.sample_adif, self.activator)
        
        # Check that hunter users were created
        hunter1 = User.objects.get(callsign='SP3BLZ')
        self.assertIsNotNone(hunter1)
        
        # Check points
        stats1 = hunter1.statistics
        self.assertEqual(stats1.hunter_points, Decimal('1.0'))
        self.assertEqual(stats1.total_hunter_qso, 1)
    
    def test_activator_points_awarded(self):
        """Test that activator points are awarded"""
        service = LogImportService()
        service.process_adif_upload(self.sample_adif, self.activator)
        
        # Check activator points
        self.activator.refresh_from_db()
        stats = self.activator.statistics
        self.assertEqual(stats.activator_points, Decimal('2.0'))  # 2 QSOs
        self.assertEqual(stats.total_activator_qso, 2)
    
    def test_security_check(self):
        """Test that users can only upload their own logs"""
        other_user = User.objects.create_user(
            email='other@test.com',
            callsign='OTHER',
            password='testpass123'
        )
        
        service = LogImportService()
        result = service.process_adif_upload(self.sample_adif, other_user)
        
        self.assertFalse(result['success'])
        self.assertIn('only upload logs for your own callsign', result['errors'][0])
