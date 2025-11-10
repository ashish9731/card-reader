import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import numpy as np
from PIL import Image as PILImage
import pytesseract
import re
import os

# Set the minimum Kivy version
kivy.require('2.0.0')

class CardReaderApp(App):
    def build(self):
        self.title = 'Smart Visiting Card Reader'
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title_label = Label(text='📇 Smart Visiting Card Reader', 
                           size_hint_y=None, height=50,
                           font_size=24)
        main_layout.add_widget(title_label)
        
        # Instructions
        instruction_label = Label(text='Upload or capture a visiting card to extract contact information',
                                 size_hint_y=None, height=30)
        main_layout.add_widget(instruction_label)
        
        # Buttons for image input
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        self.upload_btn = Button(text='Upload Image')
        self.upload_btn.bind(on_press=self.upload_image)
        button_layout.add_widget(self.upload_btn)
        
        self.camera_btn = Button(text='Use Camera')
        self.camera_btn.bind(on_press=self.capture_image)
        button_layout.add_widget(self.camera_btn)
        
        main_layout.add_widget(button_layout)
        
        # Image display area
        self.image_display = Image(size_hint_y=0.4)
        main_layout.add_widget(self.image_display)
        
        # Extract button
        self.extract_btn = Button(text='🔍 Extract Information', 
                                 size_hint_y=None, height=50,
                                 background_color=(0.2, 0.6, 1, 1))
        self.extract_btn.bind(on_press=self.extract_information)
        main_layout.add_widget(self.extract_btn)
        
        # Results display
        self.results_layout = BoxLayout(orientation='vertical', spacing=5)
        self.results_label = Label(text='Extracted Information will appear here',
                                  text_size=(None, None))
        self.results_layout.add_widget(self.results_label)
        main_layout.add_widget(self.results_layout)
        
        # Save button
        self.save_btn = Button(text='💾 Save Contact', 
                              size_hint_y=None, height=50,
                              background_color=(0.2, 0.8, 0.2, 1))
        self.save_btn.bind(on_press=self.save_contact)
        main_layout.add_widget(self.save_btn)
        
        # Initialize variables
        self.current_image = None
        self.extracted_data = {}
        
        return main_layout
    
    def upload_image(self, instance):
        # Create file chooser popup
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        content.add_widget(filechooser)
        
        popup_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        select_btn = Button(text='Select')
        cancel_btn = Button(text='Cancel')
        
        popup_layout.add_widget(select_btn)
        popup_layout.add_widget(cancel_btn)
        
        content.add_widget(popup_layout)
        
        popup = Popup(title='Choose an image', content=content, size_hint=(0.9, 0.9))
        
        def select_image(*args):
            if filechooser.selection:
                self.load_image(filechooser.selection[0])
                popup.dismiss()
        
        def cancel(*args):
            popup.dismiss()
            
        select_btn.bind(on_press=select_image)
        cancel_btn.bind(on_press=cancel)
        
        popup.open()
    
    def capture_image(self, instance):
        # For iOS, we'll simulate this with a placeholder
        # In a real implementation, you would use the camera API
        popup = Popup(title='Camera',
                      content=Label(text='Camera functionality would be implemented here\n(Tap to close)', 
                                   on_touch_down=lambda *args: popup.dismiss()),
                      size_hint=(0.8, 0.6))
        popup.open()
    
    def load_image(self, filepath):
        # Load and display image
        self.current_image = PILImage.open(filepath)
        # Convert PIL image to Kivy texture
        # This is a simplified version - in practice, you'd need more robust conversion
        self.image_display.source = filepath
        self.image_display.reload()
    
    def extract_information(self, instance):
        if self.current_image is None:
            popup = Popup(title='Error',
                          content=Label(text='Please upload an image first'),
                          size_hint=(0.6, 0.4))
            popup.open()
            return
            
        try:
            # Preprocess image
            processed_image = self.preprocess_image(self.current_image)
            
            # Extract text using pytesseract
            extracted_text = pytesseract.image_to_string(processed_image)
            
            if not extracted_text.strip():
                popup = Popup(title='Error',
                              content=Label(text='No text found in the image'),
                              size_hint=(0.6, 0.4))
                popup.open()
                return
            
            # Extract fields
            self.extracted_data = self.extract_all_fields(extracted_text)
            
            # Display results
            result_text = f"""
Name: {self.extracted_data.get('name', '')}
Email: {self.extracted_data.get('email', '')}
Phone: {self.extracted_data.get('phone', '')}
Company: {self.extracted_data.get('company', '')}
Designation: {self.extracted_data.get('designation', '')}
Website: {self.extracted_data.get('website', '')}
Address: {self.extracted_data.get('address', '')}
            """
            
            self.results_label.text = result_text
            
        except Exception as e:
            popup = Popup(title='Error',
                          content=Label(text=f'Error processing image: {str(e)}'),
                          size_hint=(0.6, 0.4))
            popup.open()
    
    def preprocess_image(self, image):
        """Enhance image for better OCR results"""
        try:
            if image.mode != 'L':
                image = image.convert('L')
            # Simple enhancement for mobile
            return image
        except Exception as e:
            return image
    
    def extract_email(self, text):
        """Extract email address from text"""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            matches = re.findall(email_pattern, text)
            return matches[0] if matches else ""
        except Exception as e:
            return ""
    
    def extract_website_from_email(self, email):
        """Extract website from email - everything after @"""
        if not email:
            return ""
        try:
            website = email.split('@')[1]
            return website
        except:
            return ""
    
    def extract_company_from_email(self, email):
        """Extract company name from email - remove TLD"""
        if not email:
            return ""
        try:
            domain = email.split('@')[1]
            company = re.sub(r'\.(com|net|org|in|co|us|uk|info|biz)$', '', domain)
            company = company.replace('-', ' ').replace('_', ' ').title()
            return company
        except:
            return ""
    
    def extract_phone_numbers(self, text):
        """Extract phone numbers from text"""
        try:
            phone_patterns = [
                r'[\+]?[9][1]?[-\s]?[6-9]\d{9}',
                r'[6-9]\d{9}',
                r'\+\d{1,3} \d{10}',
                r'\d{5} \d{5}',
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'
            ]
            
            phones = []
            for pattern in phone_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    clean_phone = re.sub(r'[^\d\+]', '', match)
                    if len(clean_phone) >= 10 and clean_phone not in phones:
                        phones.append(clean_phone)
            
            return phones[0] if phones else ""
        except Exception as e:
            return ""
    
    def extract_name(self, text_lines):
        """Extract name from text lines"""
        try:
            # Look for name in first 3 lines
            for i, line in enumerate(text_lines[:3]):
                clean_line = line.strip()
                if len(clean_line) < 2 or len(clean_line) > 50:
                    continue
                # Skip lines with emails, websites, or phone numbers
                if (re.search(r'@|www|\.com|\.net|\.org|\d{10}', clean_line.lower()) or
                    any(word in clean_line.lower() for word in ['company', 'ltd', 'inc', 'corp'])):
                    continue
                
                words = clean_line.split()
                if 1 <= len(words) <= 4:
                    # Check for proper name capitalization
                    capital_words = sum(1 for word in words if word and word[0].isupper())
                    if capital_words >= len(words) * 0.7:
                        return clean_line
            
            # Fallback: first line without obvious contact info
            for line in text_lines[:5]:
                clean_line = line.strip()
                if (len(clean_line) >= 2 and 
                    not re.search(r'@|www|\.com|\.net|\d{10}', clean_line) and
                    len(clean_line.split()) <= 4):
                    return clean_line
                    
            return ""
        except Exception as e:
            return ""
    
    def extract_designation(self, text_lines, extracted_name):
        """Extract designation from text lines"""
        try:
            designation_keywords = [
                'manager', 'director', 'engineer', 'developer', 'analyst', 'consultant', 
                'specialist', 'executive', 'officer', 'president', 'ceo', 'cto', 'cfo', 
                'vp', 'head', 'lead', 'senior', 'junior', 'associate', 'assistant',
                'architect', 'designer', 'coordinator', 'administrator', 'supervisor',
                'chief', 'partner', 'founder', 'owner', 'principal', 'neurologist', 
                'doctor', 'physician', 'surgeon', 'sales', 'marketing', 'hr', 'finance'
            ]
            
            # Find name position
            name_index = -1
            for i, line in enumerate(text_lines):
                if line.strip() == extracted_name:
                    name_index = i
                    break
            
            # Check line after name (most common)
            if name_index != -1 and name_index + 1 < len(text_lines):
                next_line = text_lines[name_index + 1].strip()
                if (2 <= len(next_line) <= 60 and 
                    not re.search(r'@|www|\.com|\.net|\d{10}', next_line.lower()) and
                    any(keyword in next_line.lower() for keyword in designation_keywords)):
                    return next_line
            
            # Check line before name
            if name_index > 0:
                prev_line = text_lines[name_index - 1].strip()
                if (2 <= len(prev_line) <= 60 and 
                    not re.search(r'@|www|\.com|\.net|\d{10}', prev_line.lower()) and
                    any(keyword in prev_line.lower() for keyword in designation_keywords)):
                    return prev_line
            
            # Search all lines for designation keywords
            for line in text_lines:
                clean_line = line.strip()
                if (clean_line != extracted_name and
                    2 <= len(clean_line) <= 60 and
                    any(keyword in clean_line.lower() for keyword in designation_keywords)):
                    if not (re.search(r'@|www|\.com|\.net', clean_line.lower()) or 
                           re.search(r'\d{10}', clean_line)):
                        return clean_line
            
            return ""
        except Exception as e:
            return ""
    
    def extract_company_name(self, text_lines, extracted_email):
        """Extract company name from text"""
        try:
            # First priority: company from email domain
            company_from_email = self.extract_company_from_email(extracted_email)
            if company_from_email:
                return company_from_email
            
            # Look for company name in prominent positions
            company_keywords = [
                'ltd', 'inc', 'corporation', 'company', 'corp', 'private', 'limited', 
                'tech', 'solutions', 'enterprises', 'group', 'industries', 'systems', 
                'technologies', 'international', 'global', 'holdings', 'ventures'
            ]
            
            # Check lines that look like company names
            for line in text_lines:
                clean_line = line.strip()
                if (3 <= len(clean_line) <= 60 and
                    not re.search(r'@|www|\.com|\.net|\d{10}', clean_line.lower())):
                    
                    # Check for company keywords
                    if any(keyword in clean_line.lower() for keyword in company_keywords):
                        return clean_line
                    
                    # Check for multi-word capitalized names
                    words = clean_line.split()
                    if len(words) >= 2:
                        capital_words = sum(1 for word in words if word and word[0].isupper())
                        if capital_words >= len(words) * 0.6:
                            return clean_line
            
            return ""
        except Exception as e:
            return ""
    
    def extract_address(self, text):
        """Extract company address from text - IMPROVED"""
        try:
            lines = text.split('\n')
            address_lines = []
            
            # More comprehensive address detection
            for i, line in enumerate(lines):
                clean_line = line.strip()
                if len(clean_line) < 5 or len(clean_line) > 100:
                    continue
                    
                # Address indicators
                has_number = bool(re.search(r'\d+', clean_line))
                has_street = bool(re.search(r'street|st|road|rd|avenue|ave|boulevard|blvd|lane|ln|drive|dr', clean_line.lower()))
                has_building = bool(re.search(r'apartment|apt|flat|building|bldg|block|sector|phase|floor|fl|suite|ste', clean_line.lower()))
                has_city = bool(re.search(r'\b(mumbai|delhi|bangalore|bengaluru|chennai|kolkata|hyderabad|pune|ahmedabad|surat|jaipur|zirakpur|mohali|chandigarh|gurgaon|noida)\b', clean_line.lower()))
                has_pincode = bool(re.search(r'\b\d{6}\b', clean_line))
                has_area = bool(re.search(r'nagar|colony|area|locality|sector|district|state', clean_line.lower()))
                
                # Calculate address score
                address_score = sum([has_number, has_street, has_building, has_city, has_pincode, has_area])
                
                # Strong indicators
                if has_pincode and has_number:
                    address_lines.append(clean_line)
                elif address_score >= 3:
                    address_lines.append(clean_line)
                elif has_number and (has_street or has_building):
                    address_lines.append(clean_line)
            
            # Clean and format address
            if address_lines:
                # Remove non-address lines
                filtered_address = []
                for line in address_lines:
                    if not re.search(r'@|http|www|\.com|\.net|gmail|yahoo', line.lower()):
                        filtered_address.append(line)
                
                if filtered_address:
                    # Join with proper formatting
                    address = ', '.join(filtered_address)
                    return address
            
            return ""
        except Exception as e:
            return ""
    
    def extract_all_fields(self, text):
        """Extract all fields from OCR text - IMPROVED"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Extract basic contact info first
            email = self.extract_email(text)
            phone = self.extract_phone_numbers(text)
            website = self.extract_website_from_email(email)
            
            # Extract name
            name = self.extract_name(lines)
            
            # Extract other fields using name as reference
            designation = self.extract_designation(lines, name)
            company = self.extract_company_name(lines, email)
            address = self.extract_address(text)
            
            return {
                'name': name or "",
                'email': email or "",
                'phone': phone or "",
                'website': website or "",
                'company': company or "",
                'designation': designation or "",
                'address': address or ""
            }
        except Exception as e:
            return {
                'name': "", 'email': "", 'phone': "", 'website': "", 
                'company': "", 'designation': "", 'address': ""
            }
    
    def save_contact(self, instance):
        if not self.extracted_data:
            popup = Popup(title='Error',
                          content=Label(text='Please extract information first'),
                          size_hint=(0.6, 0.4))
            popup.open()
            return
            
        # In a real iOS app, you would save to the device's contacts
        # For now, we'll just show a confirmation
        popup = Popup(title='Success',
                      content=Label(text='Contact information would be saved to your device'),
                      size_hint=(0.6, 0.4))
        popup.open()

# Run the app
if __name__ == '__main__':
    CardReaderApp().run()