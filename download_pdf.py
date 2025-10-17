"""
Download PDF for a specific interview session
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.comprehensive_pdf import generate_comprehensive_pdf

def main():
    session_key = "5c9603548400d9c72654b85229a9aee7"
    
    print("=" * 70)
    print(f"📄 Generating PDF for session: {session_key}")
    print("=" * 70)
    
    try:
        pdf_bytes = generate_comprehensive_pdf(session_key)
        
        if pdf_bytes:
            # Save to file
            filename = f"interview_report_{session_key}.pdf"
            with open(filename, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"\n✅ PDF generated successfully!")
            print(f"📁 Saved to: {filename}")
            print(f"📊 File size: {len(pdf_bytes)} bytes")
            print("\n" + "=" * 70)
            print(f"You can now open: {filename}")
            print("=" * 70)
        else:
            print("\n❌ PDF generation returned empty bytes")
            print("Check the logs above for errors")
    
    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

