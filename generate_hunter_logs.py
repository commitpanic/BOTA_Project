"""
Generate test ADIF logs where SP3FCK is hunter and different stations are activators.
This will test hunter points assignment.
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from bunkers.models import Bunker
from activations.adif_parser import ADIFParser
from activations.log_import_service import LogImportService

User = get_user_model()

def create_adif_log(activator_call, hunter_call, bunker_ref, qso_date, mode='SSB', band='40m', freq='7.090'):
    """Create single ADIF record"""
    return f"""<CALL:{len(hunter_call)}>{hunter_call} <QSO_DATE:8>{qso_date.strftime('%Y%m%d')} <TIME_ON:6>{qso_date.strftime('%H%M%S')} <BAND:{len(band)}>{band} <MODE:{len(mode)}>{mode} <FREQ:{len(freq)}>{freq} <RST_SENT:2>59 <RST_RCVD:2>59 <STATION_CALLSIGN:{len(activator_call)}>{activator_call} <MY_SIG:4>BOTA <MY_SIG_INFO:{len(bunker_ref)}>{bunker_ref} <EOR>
"""

def generate_and_import_logs():
    """Generate logs and import them"""
    
    print("=" * 70)
    print("GENERATING TEST LOGS - SP3FCK AS HUNTER")
    print("=" * 70)
    
    # Get or create users
    hunter, _ = User.objects.get_or_create(
        callsign='SP3FCK',
        defaults={'email': 'sp3fck@test.com'}
    )
    print(f"\n✓ Hunter: {hunter.callsign}")
    
    activators = []
    activator_calls = [
        'SP1ABC', 'SP2XYZ', 'SP5TEST', 'SQ9DEF', 'SP6GHI',
        'SP7JKL', 'SP8MNO', 'SP9PQR', 'SQ1STU', 'SQ2VWX',
        'SQ3YZA', 'SQ5BCD', 'SQ6EFG', 'SQ7HIJ', 'SQ8KLM',
        'SP3AAA', 'SP4BBB', 'SP1CCC', 'SP2DDD', 'SP5EEE',
        'SP6FFF', 'SP7GGG', 'SP8HHH', 'SP9III', 'SQ1JJJ',
        'SQ2KKK', 'SQ3LLL', 'SQ5MMM', 'SQ6NNN', 'SQ7OOO'
    ]
    
    for call in activator_calls:
        user, created = User.objects.get_or_create(
            callsign=call,
            defaults={'email': f'{call.lower()}@test.com'}
        )
        activators.append(user)
        status = "created" if created else "exists"
        print(f"✓ Activator: {call} ({status})")
    
    # Get some bunkers - need at least 25
    bunkers = list(Bunker.objects.all()[:30])
    if len(bunkers) < 25:
        print(f"\n⚠️  Warning: Only {len(bunkers)} bunkers available, need at least 25")
        print(f"    Will use {len(bunkers)} bunkers")
    
    print(f"\n✓ Using {len(bunkers)} bunkers")
    
    # Generate logs for each activator
    base_date = timezone.now() - timedelta(days=60)
    
    total_hunter_qsos = 0
    
    for idx, activator in enumerate(activators):
        if idx >= len(bunkers):
            break
            
        bunker = bunkers[idx]
        qso_date = base_date + timedelta(days=idx)
        
        print(f"\n--- Log {idx + 1}/{len(activators)}: {activator.callsign} @ {bunker.reference_number} ---")
        
        # Create ADIF content
        adif_content = f"""ADIF Export from Test Generator
<PROGRAMID:11>TestGen 1.0
<ADIF_VER:5>3.1.4
<EOH>

"""
        
        # Generate 1-3 QSOs with SP3FCK (to reach at least 50 total)
        num_qsos = 2  # Base number of QSOs per activator
        if idx < 10:  # First 10 activators make 3 QSOs
            num_qsos = 3
        
        total_hunter_qsos += num_qsos
        
        for qso_idx in range(num_qsos):
            qso_time = qso_date + timedelta(minutes=qso_idx * 5)
            modes = ['SSB', 'CW', 'FT8', 'FM']
            mode = modes[qso_idx % len(modes)]
            
            adif_content += create_adif_log(
                activator_call=activator.callsign,
                hunter_call='SP3FCK',
                bunker_ref=bunker.reference_number,
                qso_date=qso_time,
                mode=mode
            )
        
        # Save ADIF file
        filename = f'test_logs_hunter_sp3fck_{activator.callsign.lower()}.adi'
        filepath = os.path.join('media', 'test_logs', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(adif_content)
        
        print(f"  ✓ Created ADIF file: {filename}")
        print(f"  ✓ Contains {num_qsos} QSOs with SP3FCK")
        
        # Parse and import
        try:
            # Read ADIF file content
            with open(filepath, 'r', encoding='utf-8') as f:
                adif_content_str = f.read()
            
            print(f"  ✓ Read ADIF file ({len(adif_content_str)} bytes)")
            
            # Import using LogImportService
            service = LogImportService()
            result = service.process_adif_upload(
                file_content=adif_content_str,
                uploader_user=activator,
                filename=filename
            )
            
            if result['success']:
                print(f"  ✓ Imported successfully:")
                print(f"    - QSOs processed: {result['qsos_processed']}")
                print(f"    - Activator: {activator.callsign} gets {num_qsos} activator points")
                print(f"    - Hunter: SP3FCK gets {num_qsos} hunter points")
                print(f"    - Hunters updated: {result['hunters_updated']}")
            else:
                print(f"  ✗ Import failed:")
                for error in result.get('errors', []):
                    print(f"    - {error}")
            
        except Exception as e:
            print(f"  ✗ Error importing: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("LOG GENERATION AND IMPORT COMPLETE!")
    print("=" * 70)
    print(f"\nTotal QSOs generated for SP3FCK as hunter: {total_hunter_qsos}")
    print(f"Total activators used: {len(activators)}")
    print(f"Total bunkers used: {min(len(activators), len(bunkers))}")
    
    # Show statistics
    from accounts.models import UserStatistics, PointsTransaction
    
    hunter_stats = UserStatistics.objects.get(user=hunter)
    print(f"\nSP3FCK (Hunter) Statistics:")
    print(f"  - Hunter QSOs: {hunter_stats.total_hunter_qso}")
    print(f"  - Hunter Points: {hunter_stats.hunter_points}")
    print(f"  - Unique Bunkers Hunted: {hunter_stats.unique_bunkers_hunted}")
    print(f"  - Activator QSOs: {hunter_stats.total_activator_qso}")
    
    print(f"\nActivators Statistics:")
    for activator in activators:
        try:
            stats = UserStatistics.objects.get(user=activator)
            print(f"  {activator.callsign}:")
            print(f"    - Activator QSOs: {stats.total_activator_qso}")
            print(f"    - Activator Points: {stats.activator_points}")
        except UserStatistics.DoesNotExist:
            print(f"  {activator.callsign}: No stats yet")
    
    print(f"\nTotal PointsTransaction records: {PointsTransaction.objects.count()}")
    print("=" * 70)

if __name__ == '__main__':
    generate_and_import_logs()
