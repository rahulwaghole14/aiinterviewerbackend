"""
Generate PDF with proctoring warnings and snapshot images
"""
import os
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from PIL import Image
try:
    from fpdf import FPDF
except ImportError:
    try:
        from fpdf2 import FPDF
    except ImportError:
        FPDF = None


def generate_proctoring_pdf(evaluation, output_path=None):
    """
    Generate PDF with all proctoring warnings and snapshot images
    
    Args:
        evaluation: Evaluation model instance (can be temporary/unsaved)
        output_path: Optional path to save PDF (defaults to media/proctoring_pdfs/)
    
    Returns:
        str: Relative path to generated PDF file (for URL generation)
    """
    if FPDF is None:
        print("❌ FPDF not available for PDF generation")
        return None
    
    try:
        # Get proctoring warnings from evaluation
        if not evaluation.details or not isinstance(evaluation.details, dict):
            print("⚠️ No proctoring details found in evaluation")
            return None
        
        proctoring = evaluation.details.get('proctoring', {})
        warnings = proctoring.get('warnings', [])
        
        if not warnings:
            print("⚠️ No proctoring warnings to include in PDF")
            return None
        
        # Create PDF with proper page setup (A4 format)
        pdf = FPDF(format='A4', orientation='P')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Set consistent margins
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.set_top_margin(15)
        
        # Header (centered)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Proctoring Warnings Report", ln=1, align="C")
        pdf.ln(5)
        
        # Interview details (left-aligned)
        pdf.set_font("Arial", "", 10)
        candidate_name = evaluation.interview.candidate.full_name if evaluation.interview and evaluation.interview.candidate else "Unknown Candidate"
        pdf.cell(0, 5, f"Candidate: {candidate_name}", ln=1, align="L")
        
        # Handle created_at (may not exist for temporary evaluation)
        if hasattr(evaluation, 'created_at') and evaluation.created_at:
            pdf.cell(0, 5, f"Interview Date: {evaluation.created_at.strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align="L")
        else:
            from django.utils import timezone
            pdf.cell(0, 5, f"Report Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align="L")
        
        pdf.cell(0, 5, f"Total Warnings: {len(warnings)}", ln=1, align="L")
        pdf.ln(10)
        
        # Group warnings by type
        warnings_by_type = {}
        for warning in warnings:
            warning_type = warning.get('warning_type', 'unknown')
            if warning_type not in warnings_by_type:
                warnings_by_type[warning_type] = []
            warnings_by_type[warning_type].append(warning)
        
        # Add warnings section (left-aligned)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Proctoring Warnings by Type", ln=1, align="L")
        pdf.ln(5)
        
        # Process each warning type
        for warning_type, warning_list in warnings_by_type.items():
            # Warning type header (left-aligned with background)
            display_name = warning_list[0].get('display_name', warning_type.replace('_', ' ').title())
            pdf.set_font("Arial", "B", 11)
            pdf.set_fill_color(255, 243, 205)  # Light yellow background
            pdf.cell(0, 8, f"{display_name} ({len(warning_list)} occurrence(s))", ln=1, fill=True, align="L")
            pdf.ln(3)
            
            # Add images for this warning type with proper alignment
            images_per_row = 2
            image_width = 85
            image_height = 65
            x_spacing = 10  # Space between images
            y_start = pdf.get_y()
            row_height = image_height + 20  # Image height + timestamp space
            
            # Calculate page width and center images
            page_width = 210  # A4 width in mm
            margin_left = 15
            margin_right = 15
            available_width = page_width - margin_left - margin_right
            total_images_width = (images_per_row * image_width) + ((images_per_row - 1) * x_spacing)
            
            # Center images horizontally if they don't fill full width
            if total_images_width < available_width:
                x_start = margin_left + (available_width - total_images_width) / 2
            else:
                x_start = margin_left
            
            current_x = x_start
            current_y = y_start
            
            for idx, warning in enumerate(warning_list):
                snapshot = warning.get('snapshot')
                if not snapshot:
                    continue
                
                # Get full path to snapshot
                snapshot_path = os.path.join(settings.MEDIA_ROOT, 'proctoring_snaps', snapshot)
                
                # If file doesn't exist, try to get from snapshot_image field (fallback)
                if not os.path.exists(snapshot_path):
                    # Try to get from WarningLog's snapshot_image field
                    snapshot_image_path = None
                    try:
                        from interview_app.models import WarningLog
                        warning_type = warning.get('warning_type')
                        timestamp_str = warning.get('timestamp', '')
                        # Try to find the WarningLog entry
                        # Note: We need the session, but we can try to find it from evaluation
                        if evaluation.interview:
                            from interview_app.models import InterviewSession
                            try:
                                session = InterviewSession.objects.filter(
                                    interview__id=evaluation.interview.id
                                ).first()
                                if session:
                                    warning_log = WarningLog.objects.filter(
                                        session=session,
                                        warning_type=warning_type,
                                        snapshot=snapshot
                                    ).first()
                                    if warning_log and warning_log.snapshot_image:
                                        snapshot_image_path = warning_log.snapshot_image.path
                            except Exception as e:
                                print(f"⚠️ Error accessing snapshot_image field: {e}")
                    except Exception as e:
                        print(f"⚠️ Error trying snapshot_image fallback: {e}")
                    
                    if snapshot_image_path and os.path.exists(snapshot_image_path):
                        snapshot_path = snapshot_image_path
                        print(f"✅ Using snapshot_image field: {snapshot_path}")
                    else:
                        print(f"⚠️ Snapshot not found: {snapshot_path}")
                        continue
                
                try:
                    # Check if we need a new page
                    if current_y + row_height > 270:  # Leave margin at bottom
                        pdf.add_page()
                        current_y = 15
                        current_x = x_start
                    
                    # Add image to PDF with proper alignment
                    pdf.image(snapshot_path, x=current_x, y=current_y, w=image_width, h=image_height)
                    
                    # Add timestamp below image (centered)
                    pdf.set_font("Arial", "", 8)
                    timestamp = warning.get('timestamp', '')
                    if timestamp:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp_str = dt.strftime('%H:%M:%S')
                        except:
                            timestamp_str = timestamp[:8] if len(timestamp) > 8 else timestamp
                    else:
                        timestamp_str = "N/A"
                    
                    # Center timestamp text below image
                    text_width = pdf.get_string_width(f"Time: {timestamp_str}")
                    text_x = current_x + (image_width - text_width) / 2
                    pdf.text(text_x, current_y + image_height + 5, f"Time: {timestamp_str}")
                    
                    # Move to next position
                    current_x += image_width + x_spacing
                    if (idx + 1) % images_per_row == 0:
                        current_x = x_start
                        current_y += row_height
                    
                except Exception as e:
                    print(f"⚠️ Error adding image {snapshot}: {e}")
                    continue
            
            # Move to next line after images (only if we have more warning types)
            if current_x > x_start:  # If we're in the middle of a row, move to next row
                current_y += row_height
            pdf.set_y(current_y)
            pdf.ln(5)
        
        # Generate output filename
        if output_path is None:
            # Ensure MEDIA_ROOT is a Path object or string
            media_root = str(settings.MEDIA_ROOT)
            pdf_dir = os.path.join(media_root, 'proctoring_pdfs')
            # Create directory if it doesn't exist
            try:
                os.makedirs(pdf_dir, exist_ok=True)
                print(f"📁 PDF directory created/verified: {pdf_dir}")
            except Exception as e:
                print(f"❌ Error creating PDF directory {pdf_dir}: {e}")
                return None
            
            interview_id = evaluation.interview.id if evaluation.interview else 'unknown'
            filename = f"proctoring_report_{interview_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(pdf_dir, filename)
            print(f"📄 PDF will be saved to: {output_path}")
        
        # Generate PDF bytes
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin-1')
        else:
            pdf_bytes = bytes(pdf_output)
        print(f"✅ Proctoring PDF generated: {len(pdf_bytes)} bytes")
        
        # Upload to Google Cloud Storage if configured
        gcs_url = None
        try:
            from interview_app.gcs_storage import upload_pdf_to_gcs
            interview_id = evaluation.interview.id if evaluation.interview else 'unknown'
            gcs_file_path = f"proctoring_pdfs/proctoring_report_{interview_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            gcs_url = upload_pdf_to_gcs(pdf_bytes, gcs_file_path)
            if gcs_url:
                print(f"✅ PDF uploaded to GCS: {gcs_url}")
        except Exception as e:
            print(f"⚠️ Error uploading to GCS (will save locally): {e}")
        
        # Also save locally as fallback
        try:
            pdf.output(output_path)
            print(f"✅ Proctoring PDF saved locally: {output_path}")
            
            # Verify file exists
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ PDF file verified: {file_size} bytes")
            else:
                print(f"⚠️ WARNING: PDF file not found at {output_path}")
        except Exception as e:
            print(f"⚠️ Error saving PDF locally: {e}")
        
        # Return GCS URL if available, otherwise return relative path
        if gcs_url:
            return {'gcs_url': gcs_url, 'local_path': os.path.relpath(output_path, settings.MEDIA_ROOT).replace('\\', '/')}
        
        # Return relative path for URL (e.g., "proctoring_pdfs/filename.pdf")
        relative_path = os.path.relpath(output_path, settings.MEDIA_ROOT).replace('\\', '/')
        print(f"🔗 Relative path for URL: {relative_path}")
        return relative_path
        
    except Exception as e:
        print(f"❌ Error generating proctoring PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

