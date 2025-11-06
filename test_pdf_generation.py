"""
Test PDF generation for diploma certificates
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from diplomas.models import DiplomaType, Diploma
from datetime import date

User = get_user_model()


class PDFGenerationTest(TestCase):
    """Test diploma certificate PDF generation"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data"""
        # Create test user
        cls.user = User.objects.create_user(
            email="test@example.com",
            callsign="SP1TEST",
            password="testpass123"
        )
        
        # Create diploma type
        cls.diploma_type = DiplomaType.objects.create(
            name_en="Bronze Bunker Award",
            name_pl="Brązowy Medal Bunkrowy",
            description_en="Awarded for activating 10 bunkers",
            description_pl="Przyznawany za aktywację 10 bunkrów",
            category="activator",
            min_activator_points=100,
            min_hunter_points=0,
            min_b2b_points=0,
            is_active=True
        )
        
        # Create diploma
        cls.diploma = Diploma.objects.create(
            user=cls.user,
            diploma_type=cls.diploma_type,
            issue_date=date.today(),
            diploma_number="BOTA-2025-0001"
        )
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.client.login(email="test@example.com", password="testpass123")
    
    def test_pdf_download_view_exists(self):
        """Test that PDF download endpoint exists"""
        response = self.client.get(f'/diplomas/{self.diploma.id}/download/', follow=True)
        self.assertEqual(response.status_code, 200)
        print("\n✅ PDF download endpoint accessible")
    
    def test_pdf_content_type(self):
        """Test that response is PDF"""
        response = self.client.get(f'/diplomas/{self.diploma.id}/download/', follow=True)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        print("✅ Response content type is application/pdf")
    
    def test_pdf_filename(self):
        """Test that PDF has correct filename"""
        response = self.client.get(f'/diplomas/{self.diploma.id}/download/', follow=True)
        if 'Content-Disposition' in response:
            expected_filename = f'BOTA_Diploma_{self.diploma.diploma_number}.pdf'
            self.assertIn(expected_filename, response['Content-Disposition'])
            print(f"✅ PDF filename correct: {expected_filename}")
        else:
            print(f"⚠️  No Content-Disposition header (response type: {response['Content-Type']})")
    
    def test_pdf_content_not_empty(self):
        """Test that PDF has content"""
        response = self.client.get(f'/diplomas/{self.diploma.id}/download/', follow=True)
        self.assertGreater(len(response.content), 0)
        if response['Content-Type'] == 'application/pdf':
            self.assertTrue(response.content.startswith(b'%PDF'))
            print(f"✅ PDF generated with {len(response.content)} bytes")
        else:
            print(f"⚠️  Response is not PDF: {response['Content-Type']}")
    
    def test_pdf_with_polish_characters(self):
        """Test PDF generation with Polish characters"""
        # Create diploma type with Polish characters
        polish_diploma_type = DiplomaType.objects.create(
            name_en="Silver Award",
            name_pl="Srebrny Medal Łączności",
            description_en="For excellence",
            description_pl="Za doskonałość w łączności",
            category="hunter",
            min_hunter_points=200,
            is_active=True
        )
        
        polish_diploma = Diploma.objects.create(
            user=self.user,
            diploma_type=polish_diploma_type,
            issue_date=date.today(),
            diploma_number="BOTA-2025-0002"
        )
        
        response = self.client.get(f'/diplomas/{polish_diploma.id}/download/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
        print("✅ PDF with Polish characters generated successfully")
    
    def test_user_cannot_download_others_diploma(self):
        """Test that users can only download their own diplomas"""
        # Create another user
        other_user = User.objects.create_user(
            email="other@example.com",
            callsign="SP2TEST",
            password="testpass123"
        )
        
        # Create diploma for other user
        other_diploma = Diploma.objects.create(
            user=other_user,
            diploma_type=self.diploma_type,
            issue_date=date.today(),
            diploma_number="BOTA-2025-0003"
        )
        
        # Try to access other user's diploma (should redirect to login, then 404)
        response = self.client.get(f'/diplomas/{other_diploma.id}/download/', follow=True)
        # After following redirects, should end at login or 404
        self.assertNotEqual(response['Content-Type'], 'application/pdf')
        print("✅ Users cannot access other users' diplomas")
    
    def test_qr_code_in_pdf(self):
        """Test that QR code is included in PDF"""
        response = self.client.get(f'/diplomas/{self.diploma.id}/download/', follow=True)
        # QR codes generate PNG headers in PDF
        # Check if PDF contains image data (basic check)
        self.assertIn(b'/Image', response.content)
        print("✅ PDF contains image data (QR code)")


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
    django.setup()
    
    from django.test.utils import get_runner
    TestRunner = get_runner(django.conf.settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
