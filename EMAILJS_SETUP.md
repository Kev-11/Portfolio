# EmailJS Setup Guide

This portfolio now uses EmailJS for sending contact form emails directly from the client-side.

## Setup Steps

### 1. Create EmailJS Account
1. Go to [https://www.emailjs.com/](https://www.emailjs.com/)
2. Sign up for a free account (allows 200 emails/month)

### 2. Add Email Service
1. Go to **Email Services** in the EmailJS dashboard
2. Click **Add New Service**
3. Choose **Gmail** (or your preferred email provider)
4. Connect your Gmail account: `ultkev0@gmail.com`
5. Note the **Service ID** (e.g., `service_abc123`)

### 3. Create Email Template
1. Go to **Email Templates** in the dashboard
2. Click **Create New Template**
3. Use this template structure:

**Subject:**
```
New Portfolio Contact: {{subject}}
```

**Content (HTML):**
```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #0a192f;">New Contact Form Submission</h2>
    
    <div style="background: #f4f4f4; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Name:</strong> {{from_name}}</p>
        <p><strong>Email:</strong> {{from_email}}</p>
        <p><strong>Subject:</strong> {{subject}}</p>
        
        <div style="background: white; padding: 15px; margin-top: 15px; border-left: 4px solid #64ffda;">
            <p><strong>Message:</strong></p>
            <p>{{message}}</p>
        </div>
    </div>
    
    <p style="color: #666; font-size: 12px;">Reply to this email to respond directly to {{from_email}}</p>
</div>
```

4. Set **To Email** to: `{{to_email}}`
5. Set **Reply To** to: `{{from_email}}`
6. Note the **Template ID** (e.g., `template_xyz789`)

### 4. Get Public Key
1. Go to **Account** → **General** in the dashboard
2. Find your **Public Key** (e.g., `AbC123XyZ456`)

### 5. Update Frontend Configuration
Open `frontend/js/main.js` and replace these values (around line 377):

```javascript
const EMAILJS_PUBLIC_KEY = 'YOUR_PUBLIC_KEY';      // Replace with your Public Key
const EMAILJS_SERVICE_ID = 'YOUR_SERVICE_ID';      // Replace with your Service ID
const EMAILJS_TEMPLATE_ID = 'YOUR_TEMPLATE_ID';    // Replace with your Template ID
```

### 6. Test the Setup
1. Save all changes
2. Refresh your portfolio website
3. Fill out the contact form and submit
4. Check your Gmail inbox for the message
5. You can also check the EmailJS dashboard to see sent emails

## Template Parameters Used

The contact form sends these parameters to EmailJS:
- `from_name` - Visitor's name
- `from_email` - Visitor's email address
- `subject` - Message subject
- `message` - The message content
- `to_email` - Your email (ultkev0@gmail.com)

## Benefits of EmailJS

✅ **No backend SMTP configuration needed**
✅ **No App Passwords or security concerns**
✅ **Free tier: 200 emails/month**
✅ **Built-in spam protection**
✅ **Email delivery tracking in dashboard**
✅ **Multiple email services supported**
✅ **Works from static hosting (Vercel, Netlify, etc.)**

## Current Setup

- ✅ EmailJS SDK loaded in `index.html`
- ✅ Contact form updated to use EmailJS in `main.js`
- ✅ Backend still saves submissions to database (for admin panel viewing)
- ✅ Rate limiting: 100 submissions/hour per IP

## Troubleshooting

**Email not sending?**
- Check browser console for errors
- Verify all 3 credentials are correct in `main.js`
- Check EmailJS dashboard for delivery status
- Make sure you're within the 200 emails/month limit

**Want to see sent emails?**
- Log into EmailJS dashboard
- Go to **Email History** to see all sent emails
