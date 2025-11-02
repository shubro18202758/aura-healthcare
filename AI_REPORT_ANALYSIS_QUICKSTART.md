# Quick Start Guide: AI Report Analysis Assistant

## 🚀 Getting Started

### Prerequisites
- Backend server running on `http://127.0.0.1:8000`
- Frontend server running on `http://localhost:5173`
- Doctor account logged in
- At least one auto-generated medical report available

### Step-by-Step Testing

#### 1. Access Medical Reports

```
1. Log in as a doctor
2. Navigate to "Medical Reports" tab in Doctor Dashboard
3. You should see a list of generated reports
```

#### 2. Open AI Assistant

```
1. Click "View Report" on any report card
2. A modal opens with two tabs:
   - "Report Details" (default)
   - "Ask AI Assistant"
3. Click "Ask AI Assistant" tab
```

#### 3. Test Quick Queries

The AI Assistant has pre-built quick query buttons. Try them:

```
Click any quick query button:
- "What are the main symptoms reported?"
- "Are there any urgent findings?"
- "What tests were recommended?"
- "Summarize the key clinical points"
- "What medications were discussed?"
- "Are there any red flags?"
```

**Expected Result**: AI response appears in conversation format within 2-5 seconds

#### 4. Test Custom Queries

Type your own questions in the text area:

```
Example queries to try:
- "What allergies does the patient have?"
- "Are there any drug interactions to be aware of?"
- "What's the diagnosis?"
- "What follow-up is recommended?"
- "Summarize the patient's medical history"
```

**How to send**:
- Press `Enter` to send
- Or click the send button
- Use `Shift+Enter` for new line

**Expected Result**: Conversation history builds up with user questions and AI responses

#### 5. Test Summary Generation

Switch to "Generate Summary" tab:

```
1. Click "Generate Summary" tab at the top
2. Select one of 6 summary types:
   - 📝 Brief Summary (quick 3-4 sentences)
   - 📄 Detailed Summary (comprehensive)
   - 🔍 Key Findings (bullet points)
   - ⚠️ Urgent Items (critical only)
   - 🩺 Differential Diagnoses
   - 💊 Recommendations (tests, follow-ups)
3. Click "Generate Summary" button
```

**Expected Result**: Summary appears with timestamp within 5-10 seconds

#### 6. Test Multiple Summary Types

```
1. Generate "Brief Summary"
2. Then generate "Key Findings"
3. Then generate "Urgent Items"
```

**Expected Result**: All summaries appear in results section with different timestamps

#### 7. Test Error Handling

Intentionally trigger errors to verify error handling:

```
Test 1: Empty query
- Leave text area empty and click send
- Should show validation error

Test 2: Very long query (>1000 characters)
- Type or paste a very long question
- Should either truncate or show error

Test 3: Network error (optional)
- Disconnect internet briefly
- Try to send query
- Should show "Failed to connect" error
```

## 🧪 Advanced Testing

### Test Conversation Flow

```
1. Ask: "What are the main symptoms?"
2. Wait for response
3. Ask follow-up: "How severe are they?"
4. Ask another follow-up: "What's your recommendation?"
```

**Expected Result**: Context is maintained, AI can reference previous responses

### Test Tab Switching

```
1. Start in "Ask Questions" tab
2. Ask a question
3. Switch to "Generate Summary" tab
4. Generate a summary
5. Switch back to "Ask Questions" tab
```

**Expected Result**: 
- Conversation history preserved when switching back
- Summary results preserved
- No state loss

### Test Loading States

```
1. Send a complex query
2. Observe typing indicator (three animated dots)
3. Should appear immediately after sending
4. Should disappear when response arrives
```

### Test Responsive Design

```
1. Resize browser window to mobile size
2. Check if layout adapts properly
3. Test on actual mobile device if possible
```

**Expected Result**: Component remains usable on small screens

## 🔍 Verification Checklist

### Backend Verification

Open backend logs and verify:

```bash
# Check if API calls are being made
- POST /api/reports/analyze/{report_id}
- POST /api/reports/summarize/{report_id}

# Check for successful responses (200 status)
# Check for proper error handling (404, 401, 500)
```

### Frontend Verification

Open browser console (F12) and check:

```javascript
// No JavaScript errors
// Successful API calls logged
// State updates properly
// No memory leaks
```

### Database Verification

Check MongoDB collections:

```javascript
// Reports collection should have:
- report_id
- patient_id
- doctor_id (optional)
- summary
- findings
- metadata
- status

// No duplicate reports created
// Timestamps are accurate
```

## 🐛 Common Issues & Solutions

### Issue 1: "Failed to analyze report"

**Possible Causes**:
- API key not configured
- Report doesn't exist
- Unauthorized access

**Solution**:
```bash
# Check .env file
GOOGLE_REPORTS_API_KEY=AIzaSyDZsg6GCE0p_uWCEDCTMg73M-KLceLRtcE

# Restart backend
cd backend
uvicorn app.main:app --reload
```

### Issue 2: Slow Response Times

**Expected**:
- Simple queries: 2-5 seconds
- Summaries: 5-10 seconds
- Complex queries: 8-15 seconds

**If slower**:
- Check internet connection
- Check API rate limits
- Check report size (large reports = longer processing)

### Issue 3: Tab Not Switching

**Solution**:
```
1. Refresh the page (F5)
2. Check browser console for errors
3. Verify component is properly imported
4. Clear browser cache
```

### Issue 4: Conversation Not Displaying

**Solution**:
```
1. Check if ReportAnalyzer is receiving reportId prop
2. Verify API response in Network tab
3. Check state updates in React DevTools
4. Ensure CSS is loaded (check styling)
```

## 📊 Performance Benchmarks

### Expected Performance:

| Operation | Expected Time | Status |
|-----------|--------------|--------|
| Quick Query | 2-5 seconds | ✅ |
| Custom Query | 3-7 seconds | ✅ |
| Brief Summary | 3-5 seconds | ✅ |
| Detailed Summary | 5-10 seconds | ✅ |
| Key Findings | 4-6 seconds | ✅ |
| Urgent Items | 3-5 seconds | ✅ |
| Differential Diagnoses | 6-9 seconds | ✅ |
| Recommendations | 5-8 seconds | ✅ |
| Report Comparison | 8-15 seconds | 🔧 (Future) |

### UI Responsiveness:

| Interaction | Expected Time | Status |
|------------|--------------|--------|
| Tab Switch | Instant (<100ms) | ✅ |
| Button Click | Instant (<50ms) | ✅ |
| Typing Indicator | Shows immediately | ✅ |
| Error Banner | Shows immediately | ✅ |
| Modal Open | ~200ms animation | ✅ |
| Modal Close | ~200ms animation | ✅ |

## 🎯 Success Criteria

Feature is working correctly if:

- ✅ All quick queries return relevant responses
- ✅ Custom queries work with natural language
- ✅ All 6 summary types generate successfully
- ✅ Conversation history is maintained
- ✅ Loading indicators appear during processing
- ✅ Error messages are clear and helpful
- ✅ Tab switching works smoothly
- ✅ Mobile layout is usable
- ✅ No console errors
- ✅ Response times are within expected ranges

## 📞 Support

If you encounter issues:

1. **Check Logs**:
   - Backend: `backend/logs/` or console output
   - Frontend: Browser console (F12)

2. **Verify Configuration**:
   - `.env` file has correct API keys
   - Backend server is running
   - Frontend server is running
   - Database is connected

3. **Review Documentation**:
   - `AI_REPORT_ANALYSIS_DOCUMENTATION.md`
   - `AUTOMATED_REPORT_GENERATION.md`

4. **Test Individual Components**:
   - Backend endpoints with Postman/curl
   - Frontend components in isolation
   - Database queries directly

## 🎉 Next Steps

Once basic testing is complete:

1. **User Acceptance Testing**: Have actual doctors test the feature
2. **Collect Feedback**: Note areas for improvement
3. **Performance Monitoring**: Track API usage and response times
4. **Feature Enhancements**: Implement comparison functionality
5. **Documentation Updates**: Keep docs current with changes

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Tested**: ✅ Ready for UAT
