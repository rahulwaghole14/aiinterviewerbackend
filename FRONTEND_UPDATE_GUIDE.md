# Frontend Update Guide - AI Evaluation Display

## 📋 Current Status

The backend is **fully implemented** and ready. The frontend needs a small update to show:
1. AI Evaluation (from `evaluation` object)
2. Proctoring Warnings with images
3. PDF download link

---

## ✅ Backend Implementation Complete

### API Endpoint:
```
GET /api/evaluation/reports/{interview_id}/
```

### Response Structure:
```json
{
  "id": 1,
  "interview": 123,
  "overall_score": 7.5,
  "traits": "Strengths: ...\nWeaknesses: ...",
  "suggestions": "Continue building...",
  "proctoring_warnings": [
    {
      "warning_type": "multiple_people",
      "timestamp": "2025-11-04T18:04:15",
      "snapshot": "filename.jpg",
      "snapshot_url": "/media/proctoring_snaps/filename.jpg",
      "display_name": "Multiple People"
    }
  ],
  "proctoring_pdf_url": "/media/proctoring_pdfs/proctoring_report_123_20251104_180000.pdf",
  "details": {
    "ai_analysis": {...},
    "proctoring": {...}
  }
}
```

---

## 🔧 Frontend Update Required

### File: `frontend/src/components/CandidateDetails.jsx`

### 1. Update Evaluation Fetch to Include Proctoring Details

**Current**: Fetches from `/api/evaluations/` (CRUD endpoint)
**Update**: Also fetch detailed evaluation from `/api/evaluation/report/{interview_id}/` for proctoring details

**Location**: Around line 130-140 in `fetchInterviews` function

**Add**:
```javascript
// After fetching evaluations, fetch detailed reports for proctoring data
const evaluationReports = await Promise.all(
  candidateInterviews.map(async (interview) => {
    if (interview.evaluation) {
      try {
        const reportResponse = await fetch(
          `${baseURL}/api/evaluation/report/${interview.id}/`,
          {
            headers: {
              Authorization: `Token ${authToken}`,
              "Content-Type": "application/json",
            },
          }
        );
        if (reportResponse.ok) {
          return await reportResponse.json();
        }
      } catch (error) {
        console.error("Error fetching evaluation report:", error);
      }
    }
    return null;
  })
);
```

### 2. Update Evaluation Display Section

**Location**: Around line 933-976 (Manual Evaluation Section)

**Change "Manual Evaluation Results" to "AI Evaluation"**:
```jsx
{/* AI Evaluation Section */}
{interviews.some((i) => i.evaluation) && (
  <div className="evaluation-info">
    <div className="evaluation-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
      <h4 style={{ color: 'var(--color-primary)', fontSize: '1.2rem', fontWeight: '600', margin: 0 }}>AI Evaluation Results</h4>
      {/* ... existing score display ... */}
    </div>
    
    {/* ... existing score, traits, suggestions ... */}
    
    {/* Add Proctoring Warnings Section */}
    {interview.evaluation.details?.proctoring?.warnings && (
      <div className="proctoring-warnings-section" style={{ marginTop: '20px', padding: '15px', background: '#fff3cd', borderRadius: '8px' }}>
        <h5 style={{ marginBottom: '10px', color: '#856404' }}>
          Proctoring Warnings ({interview.evaluation.details.proctoring.total_warnings || 0})
        </h5>
        
        {/* Group warnings by type */}
        {Object.entries(
          interview.evaluation.details.proctoring.warnings.reduce((acc, warning) => {
            const type = warning.warning_type || 'unknown';
            if (!acc[type]) acc[type] = [];
            acc[type].push(warning);
            return acc;
          }, {})
        ).map(([type, warnings]) => (
          <div key={type} style={{ marginBottom: '15px' }}>
            <strong style={{ color: '#856404' }}>
              {warnings[0].display_name || type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </strong>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '10px' }}>
              {warnings.map((warning, idx) => (
                warning.snapshot_url && (
                  <div key={idx} style={{ position: 'relative' }}>
                    <img
                      src={`${baseURL}${warning.snapshot_url}`}
                      alt={warning.display_name}
                      style={{
                        width: '120px',
                        height: '90px',
                        objectFit: 'cover',
                        borderRadius: '4px',
                        border: '2px solid #ffc107',
                        cursor: 'pointer'
                      }}
                      onClick={() => window.open(`${baseURL}${warning.snapshot_url}`, '_blank')}
                    />
                    <div style={{ fontSize: '0.75em', color: '#856404', marginTop: '5px', textAlign: 'center' }}>
                      {new Date(warning.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        ))}
      </div>
    )}
    
    {/* Add PDF Download Link */}
    {interview.evaluation.details?.proctoring_pdf_url && (
      <div style={{ marginTop: '15px' }}>
        <a
          href={`${baseURL}${interview.evaluation.details.proctoring_pdf_url}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            padding: '10px 20px',
            background: '#28a745',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '5px',
            fontWeight: '600'
          }}
        >
          📄 Download Proctoring Report (PDF)
        </a>
      </div>
    )}
  </div>
)}
```

---

## 📝 Summary

### Backend ✅ Complete
- Coding language selection fixed
- AI evaluation automatically created after interview
- Proctoring PDF generation implemented
- API endpoints ready

### Frontend 🔄 Needs Update
- Update evaluation display to show as "AI Evaluation"
- Add proctoring warnings section with images
- Add PDF download link

---

## 🚀 Quick Test

1. Complete an interview
2. Check database: `Evaluation.objects.all()`
3. Verify PDF exists: `media/proctoring_pdfs/`
4. Test API: `GET /api/evaluation/report/{interview_id}/`
5. Check frontend shows evaluation

---

## 📦 Required Dependencies

Make sure these are installed:
```bash
pip install fpdf2 Pillow
```










































