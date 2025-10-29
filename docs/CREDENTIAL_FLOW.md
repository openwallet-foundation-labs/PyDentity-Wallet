# PyDentity Wallet - Credential Issuance Flow

## Overview

The PyDentity Wallet now implements a Bifold-like credential issuance flow with dedicated screens for viewing and accepting/declining credential offers.

## Flow Comparison

### Bifold Wallet Flow
1. User scans connection QR code → Connection established
2. Issuer sends credential offer → Notification appears
3. User taps notification → Opens **CredentialOffer screen**
4. User views credential details → Can see attributes, issuer info
5. User accepts/declines → Processing modal → Returns to credential list

### PyDentity Wallet Flow (NEW)
1. User scans connection QR code → Connection established  
2. Issuer sends credential offer → Notification appears
3. User taps "View Details" → Opens **/credential-offer/<exchange_id> page**
4. User views credential preview → Can see attributes, issuer info
5. User accepts/declines → Processing modal → Returns to home/credential list

## Implementation

### New Files Created

#### 1. **Credential Offer Page**
`app/templates/pages/credential-offer.jinja`

Features:
- Full-screen dedicated page for credential offer
- Credential preview card with attributes
- Issuer information display
- "What You're Receiving" information section
- Large Accept/Decline action buttons
- Processing modal with visual feedback
- Similar layout and UX to Bifold's CredentialOffer screen

### Modified Files

#### 2. **Routes** (`app/routes/main/__init__.py`)

**New Route:**
```python
@bp.route("/credential-offer/<exchange_id>", methods=["GET"])
def credential_offer(exchange_id):
    # Displays full credential offer details page
```

**Existing Routes** (unchanged):
- `POST /credential-offers/<exchange_id>/accept` - Accept credential
- `POST /credential-offers/<exchange_id>/decline` - Decline credential

#### 3. **Notification Modal** (`app/templates/components/modals/notification.jinja`)

**Changed:**
- Credential offer notifications now show "View Details" button
- Button navigates to dedicated credential offer page
- Removed inline Accept/Decline buttons from notification list
- Provides better UX with full-screen view before decision

## User Experience Flow

### 1. Scan Connection Invitation (from anoncreds.vc)

```
User: Opens PyDentity Wallet
User: Taps "Scan QR Code" button
User: Scans anoncreds.vc connection QR
System: Establishes DIDComm connection
```

### 2. Receive Credential Offer

```
Issuer: Sends credential offer via anoncreds.vc
System: Receives credential offer
System: Creates notification
UI: Shows notification badge on home screen
```

### 3. View Credential Offer

```
User: Taps "View" on notification banner (or opens notification modal)
User: Sees credential offer in list
User: Taps "View Details" button
System: Opens /credential-offer/<exchange_id> page
UI: Displays:
  - Issuer logo and name
  - Credential name
  - All attributes being offered
  - Information about what they're receiving
  - Accept/Decline buttons
```

### 4. Accept Credential

```
User: Reviews credential details
User: Taps "Accept Credential" button
System: Shows processing modal "Accepting Credential..."
System: Calls POST /credential-offers/<exchange_id>/accept
ACA-Py: Sends credential request to issuer
System: Processing modal shows "Credential Accepted!"
System: Redirects to home page
UI: Credential now appears in "My Credentials" list
```

### 5. Decline Credential

```
User: Taps "Decline" button
System: Shows confirmation dialog
User: Confirms decline
System: Shows processing modal "Declining Offer..."
System: Calls POST /credential-offers/<exchange_id>/decline
ACA-Py: Sends decline message to issuer
System: Redirects to home page
UI: Offer removed from notifications
```

## Design Features

### Similar to Bifold

✅ **Dedicated full-screen page** for credential offers  
✅ **Credential preview card** showing all attributes  
✅ **Issuer information** with avatar/logo  
✅ **Clear action buttons** (Accept/Decline)  
✅ **Processing feedback** with modal  
✅ **Visual hierarchy** with cards and proper spacing  
✅ **Informative content** explaining what user receives  

### PyDentity-Specific Enhancements

✅ **Web-based** interface (not mobile-only)  
✅ **Bootstrap/Tabler UI** for modern look  
✅ **Responsive design** works on mobile and desktop  
✅ **Notification system** integrated with existing pattern  
✅ **Technical details** available if needed  

## Technical Details

### Backend Integration

The credential offer page integrates with existing PyDentity plugins:

- **AgentController**: Fetches credential exchange details, sends accept/decline
- **AskarStorage**: Retrieves wallet information and credentials
- **QRScanner**: Handles connection invitation scanning

### Data Flow

```
Credential Offer Received
    ↓
Stored in ACA-Py Agent
    ↓
Notification created (via webhooks/polling)
    ↓
User clicks "View Details"
    ↓
GET /credential-offer/<exchange_id>
    ↓
Fetch offer from agent.get_credential_exchange()
    ↓
Render credential-offer.jinja with offer data
    ↓
User accepts → POST /credential-offers/<exchange_id>/accept
    ↓
Agent sends credential request
    ↓
Credential issued and stored
    ↓
Appears in "My Credentials"
```

## Future Enhancements

Potential improvements to make it even more Bifold-like:

1. **Auto-refresh** on credential offer page (check status every few seconds)
2. **Attribute icons** based on attribute types
3. **Issuer verification** show trust indicators
4. **Credential type badges** (education, ID, membership, etc.)
5. **Animation** on accept/decline actions
6. **History tracking** of accepted/declined offers
7. **Push notifications** when offers received (if web push enabled)

## Testing the Flow

1. **Start anoncreds.vc demo server**
2. **Open PyDentity Wallet**
3. **Scan connection QR** from anoncreds.vc
4. **Wait for credential offer** from anoncreds.vc
5. **View notification** in PyDentity Wallet
6. **Tap "View Details"** → Opens full credential offer page
7. **Review details** → See all attributes
8. **Tap "Accept Credential"** → Processing → Success!
9. **View credential** in "My Credentials" list

## Comparison Table

| Feature | Bifold Wallet | PyDentity Wallet |
|---------|---------------|------------------|
| Platform | Mobile (React Native) | Web (Flask/Jinja) |
| Credential Offer Screen | ✅ CredentialOffer.tsx | ✅ credential-offer.jinja |
| Full Preview | ✅ | ✅ |
| Accept/Decline | ✅ | ✅ |
| Processing Feedback | ✅ Modal | ✅ Modal |
| Attribute Display | ✅ Cards | ✅ Cards |
| Issuer Info | ✅ Avatar + Name | ✅ Avatar + Name |
| Navigation | Stack navigator | Page navigation |
| Auto-refresh | ❌ | 🔄 Can add |

The flows are now functionally equivalent with similar UX patterns!

