from app import mail, db
from flask_mail import Message
from datetime import datetime, timedelta, UTC
import secrets

def _get_email_template(template_name, **kwargs):
    """Get HTML email template with common styling"""
    base_style = """
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4CAF50, #45A049); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
        .otp-code { background: #e8f5e8; border: 2px solid #4CAF50; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; color: #2e7d32; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
    """
    
    if template_name == "verification":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            {base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎧 Podcast App</h1>
                    <p>Verify Your Email Address</p>
                </div>
                <div class="content">
                    <h2>Welcome to Podcast App!</h2>
                    <p>Thank you for signing up. To complete your registration, please verify your email address by entering the verification code below:</p>
                    
                    <div class="otp-code">
                        {kwargs.get('otp', '')}
                    </div>
                    
                    <p><strong>This verification code will expire in 10 minutes.</strong></p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        Never share this code with anyone. Our team will never ask for your verification code.
                    </div>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Podcast App. All rights reserved.</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "password_reset":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            {base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎧 Podcast App</h1>
                    <p>Reset Your Password</p>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{kwargs.get('reset_url', '')}" class="button">Reset Password</a>
                    </div>
                    
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        If you didn't request a password reset, please ignore this email.<br>
                        Never share this link with anyone.
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4CAF50;">{kwargs.get('reset_url', '')}</p>
                </div>
                <div class="footer">
                    <p>© 2025 Podcast App. All rights reserved.</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "welcome":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Podcast App</title>
            {base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎧 Podcast App</h1>
                    <p>Welcome Aboard!</p>
                </div>
                <div class="content">
                    <h2>Welcome to Podcast App!</h2>
                    <p>Hi {kwargs.get('email', 'there')},</p>
                    
                    <p>Your email has been successfully verified! You're now ready to explore the world of podcasts.</p>
                    
                    <h3>What you can do now:</h3>
                    <ul>
                        <li>🎵 Discover and listen to amazing podcasts</li>
                        <li>📝 Create and share your own podcasts</li>
                        <li>💬 Engage with the community through comments</li>
                        <li>❤️ Like and save your favorite episodes</li>
                        <li>📊 Track your listening history</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{kwargs.get('app_url', '')}" class="button">Start Exploring</a>
                    </div>
                    
                    <p>Happy listening!</p>
                    <p><strong>The Podcast App Team</strong></p>
                </div>
                <div class="footer">
                    <p>© 2025 Podcast App. All rights reserved.</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

def send_verification_email(user):
    """Send email verification with OTP"""
    # Generate a 6-digit OTP
    otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    user.otp = otp
    user.otp_expiry = datetime.now(UTC) + timedelta(minutes=10)  # OTP valid for 10 minutes
    db.session.commit()
    
    html_content = _get_email_template("verification", otp=otp)
    
    msg = Message('Verify Your Email - Podcast App',
                  sender='noreply@podcastapp.com',
                  recipients=[user.email])
    msg.html = html_content
    msg.body = f"""Verify Your Email - Podcast App

Welcome to Podcast App!

Your verification code is: {otp}

This code will expire in 10 minutes.

If you didn't create an account with us, please ignore this email.

© 2025 Podcast App. All rights reserved."""
    
    mail.send(msg)

def send_reset_password_email(user):
    """Send password reset email"""
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiry = datetime.now(UTC) + timedelta(hours=1)
    db.session.commit()
    
    # Create reset URL - you should update this to match your frontend URL
    reset_url = f"http://192.168.231.17:8000/reset-password?token={token}"
    
    html_content = _get_email_template("password_reset", reset_url=reset_url)
    
    msg = Message('Reset Your Password - Podcast App',
                  sender='noreply@podcastapp.com',
                  recipients=[user.email])
    msg.html = html_content
    msg.body = f"""Reset Your Password - Podcast App

We received a request to reset your password.

Click this link to reset your password: {reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

© 2025 Podcast App. All rights reserved."""
    
    mail.send(msg)

def send_welcome_email(user):
    """Send welcome email after successful verification"""
    app_url = "http://192.168.231.17:8000"  # Update this to match your frontend URL
    
    html_content = _get_email_template("welcome", email=user.email, app_url=app_url)
    
    msg = Message('Welcome to Podcast App!',
                  sender='noreply@podcastapp.com',
                  recipients=[user.email])
    msg.html = html_content
    msg.body = f"""Welcome to Podcast App!

Hi {user.email},

Your email has been successfully verified! You're now ready to explore the world of podcasts.

What you can do now:
- Discover and listen to amazing podcasts
- Create and share your own podcasts
- Engage with the community through comments
- Like and save your favorite episodes
- Track your listening history

Start exploring: {app_url}

Happy listening!

The Podcast App Team

© 2025 Podcast App. All rights reserved."""
    
    mail.send(msg) 