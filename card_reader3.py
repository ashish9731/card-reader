import streamlit as st
from PIL import Image, ImageEnhance
import pytesseract
import pandas as pd
import io
import base64
import os
import re
import tempfile

st.set_page_config(page_title="OCR Visiting Card Reader", layout="wide")

# Initialize session state
if 'save_path' not in st.session_state:
    st.session_state.save_path = None
if 'csv_path' not in st.session_state:
    st.session_state.csv_path = None
if 'image_folder' not in st.session_state:
    st.session_state.image_folder = None
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = {}
if 'delete_mode' not in st.session_state:
    st.session_state.delete_mode = False

st.title("📇 Smart Visiting Card Reader")
st.write("Upload or capture a visiting card to extract contact information automatically.")

# ---------- POPUP MODAL FOR SAVE LOCATION ----------
if not st.session_state.setup_complete:
    st.markdown("""
    <style>
    .setup-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="setup-container">', unsafe_allow_html=True)
        st.header("📍 Setup Save Location")
        st.warning("Please configure where to save your visiting card data before proceeding.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Option 1: Default Location")
            if st.button("📁 Use Default Folder", use_container_width=True):
                default_path = "visiting_cards_data"
                os.makedirs(default_path, exist_ok=True)
                st.session_state.save_path = default_path
                st.session_state.csv_path = os.path.join(default_path, "cards_data.csv")
                st.session_state.image_folder = os.path.join(default_path, "saved_cards")
                os.makedirs(st.session_state.image_folder, exist_ok=True)
                st.session_state.setup_complete = True
                st.rerun()
        
        with col2:
            st.subheader("Option 2: Custom Location")
            custom_path = st.text_input("Enter custom folder path:", 
                                      placeholder="C:/Users/YourName/VisitingCards")
            new_folder = st.text_input("Or create new folder:", 
                                     placeholder="my_business_cards")
            
            if st.button("✅ Set Custom Location", use_container_width=True):
                if custom_path:
                    selected_path = custom_path
                elif new_folder:
                    selected_path = new_folder
                else:
                    st.error("Please enter a folder path or name")
                    st.stop()
                
                try:
                    os.makedirs(selected_path, exist_ok=True)
                    st.session_state.save_path = selected_path
                    st.session_state.csv_path = os.path.join(selected_path, "cards_data.csv")
                    st.session_state.image_folder = os.path.join(selected_path, "saved_cards")
                    os.makedirs(st.session_state.image_folder, exist_ok=True)
                    st.session_state.setup_complete = True
                    st.success(f"✅ Save location set to: {selected_path}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating folder: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------- IMAGE PREPROCESSING FUNCTION ----------
def preprocess_image(image):
    """Enhance image for better OCR results"""
    try:
        if image.mode != 'L':
            image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        return image
    except Exception as e:
        return image

# ---------- IMPROVED EXTRACTION FUNCTIONS ----------
def extract_email(text):
    """Extract email address from text"""
    try:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    except Exception as e:
        return ""

def extract_website_from_email(email):
    """Extract website from email - everything after @"""
    if not email:
        return ""
    try:
        website = email.split('@')[1]
        return website
    except:
        return ""

def extract_company_from_email(email):
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

def extract_phone_numbers(text):
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

def extract_name(text_lines):
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

def extract_designation(text_lines, extracted_name):
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

def extract_company_name(text_lines, extracted_email):
    """Extract company name from text"""
    try:
        # First priority: company from email domain
        company_from_email = extract_company_from_email(extracted_email)
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

def extract_address(text):
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
        
        # Also look for consecutive address lines
        if len(address_lines) < 2:
            for i in range(len(lines) - 2):
                block_lines = lines[i:i+3]
                block_text = ' '.join(block_lines)
                
                block_score = 0
                if re.search(r'\d+', block_text):
                    block_score += 1
                if re.search(r'street|st|road|rd|avenue|ave', block_text.lower()):
                    block_score += 1
                if re.search(r'\b\d{6}\b', block_text):
                    block_score += 1
                if re.search(r'apartment|building|block|sector', block_text.lower()):
                    block_score += 1
                
                if block_score >= 3:
                    address_lines = [line.strip() for line in block_lines if line.strip()]
                    break
        
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

def extract_all_fields(text):
    """Extract all fields from OCR text - IMPROVED"""
    try:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract basic contact info first
        email = extract_email(text)
        phone = extract_phone_numbers(text)
        website = extract_website_from_email(email)
        
        # Extract name
        name = extract_name(lines)
        
        # Extract other fields using name as reference
        designation = extract_designation(lines, name)
        company = extract_company_name(lines, email)
        address = extract_address(text)
        
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

# ---------- DATABASE FUNCTIONS ----------
def load_database():
    """Load the database CSV"""
    if os.path.exists(st.session_state.csv_path):
        try:
            return pd.read_csv(st.session_state.csv_path)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_to_database(data):
    """Save data to CSV database"""
    try:
        # Remove Raw_Text from data
        data_to_save = {k: v for k, v in data.items() if k != 'Raw_Text'}
        
        df_row = pd.DataFrame([data_to_save])
        
        existing_df = load_database()
        if not existing_df.empty:
            updated_df = pd.concat([existing_df, df_row], ignore_index=True)
        else:
            updated_df = df_row
        
        updated_df.to_csv(st.session_state.csv_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to database: {e}")
        return False

def delete_from_database(index):
    """Delete record from database"""
    try:
        df = load_database()
        if not df.empty and 0 <= index < len(df):
            df = df.drop(index).reset_index(drop=True)
            df.to_csv(st.session_state.csv_path, index=False)
            return True
    except Exception as e:
        st.error(f"Error deleting record: {e}")
    return False

# ---------- MAIN APPLICATION ----------
st.sidebar.header("📁 Current Settings")
st.sidebar.success(f"**Save Location:**\n`{st.session_state.save_path}`")

if st.sidebar.button("🔄 Change Save Location"):
    st.session_state.setup_complete = False
    st.session_state.processed_data = {}
    st.rerun()

# Load database stats
df = load_database()
if not df.empty:
    st.sidebar.info(f"**Cards in database:** {len(df)}")
else:
    st.sidebar.info("**Cards in database:** 0")

# ---------- CARD PROCESSING INTERFACE ----------
st.header("🎯 Process Visiting Card")

option = st.radio("Choose input method:", ["Upload Image", "Use Camera"], horizontal=True)
image = None

if option == "Upload Image":
    uploaded = st.file_uploader("Choose visiting card image", type=["jpg", "jpeg", "png"])
    if uploaded:
        try:
            image = Image.open(uploaded)
            st.image(image, caption="Uploaded Card", use_column_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

elif option == "Use Camera":
    camera_input = st.camera_input("Take a picture of the visiting card")
    if camera_input:
        try:
            image = Image.open(camera_input)
            st.image(image, caption="Captured Card", use_column_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

# Process the image
if image is not None:
    if st.button("🔍 Extract Information", type="primary", use_container_width=True):
        with st.spinner("Processing card... This may take a few seconds"):
            try:
                processed_image = preprocess_image(image)
                custom_config = r'--oem 3 --psm 6'
                extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
                
                if not extracted_text.strip():
                    st.error("❌ No text found in the image. Please try with a clearer picture.")
                    st.stop()
                
                extracted_data = extract_all_fields(extracted_text)
                st.session_state.processed_data = extracted_data
                st.success("✅ Information extracted successfully!")
                
            except Exception as e:
                st.error(f"❌ Error processing image: {str(e)}")

# Show editable form if we have processed data
if st.session_state.processed_data:
    st.header("📋 Contact Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Details")
        name = st.text_input("👤 Name", value=st.session_state.processed_data.get('name', ''))
        email = st.text_input("📧 Email", value=st.session_state.processed_data.get('email', ''))
        phone = st.text_input("📞 Phone", value=st.session_state.processed_data.get('phone', ''))
        designation = st.text_input("💼 Designation", value=st.session_state.processed_data.get('designation', ''))
    
    with col2:
        st.subheader("Company Details")
        company = st.text_input("🏢 Company", value=st.session_state.processed_data.get('company', ''))
        website = st.text_input("🌐 Website", value=st.session_state.processed_data.get('website', ''))
        address = st.text_area("📍 Address", value=st.session_state.processed_data.get('address', ''), height=100,
                             placeholder="Address will be automatically detected...")
    
    if st.button("💾 Save to Database", type="primary", use_container_width=True):
        try:
            # Save image
            img_files = [f for f in os.listdir(st.session_state.image_folder) if f.startswith('card_')]
            next_number = len(img_files) + 1
            img_filename = f"card_{next_number}.png"
            img_full_path = os.path.join(st.session_state.image_folder, img_filename)
            
            img_buffer = io.BytesIO()
            image.save(img_buffer, format="PNG")
            img_bytes = img_buffer.getvalue()
            
            with open(img_full_path, "wb") as f:
                f.write(img_bytes)
            
            # Prepare data for saving
            contact_data = {
                'Name': name,
                'Email': email,
                'Phone': phone,
                'Designation': designation,
                'Company': company,
                'Website': website,
                'Address': address,
                'Image_Path': img_full_path
            }
            
            if save_to_database(contact_data):
                st.success("✅ Contact saved successfully!")
                
                # Offer downloads
                st.subheader("📥 Download Options")
                
                col_d1, col_d2, col_d3 = st.columns(3)
                
                with col_d1:
                    current_df = load_database()
                    csv_data = current_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📊 Download CSV", csv_data, "visiting_cards.csv", "text/csv")
                
                with col_d2:
                    vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
ORG:{company}
TITLE:{designation}
TEL:{phone}
EMAIL:{email}
URL:{website}
ADR:;;{address}
END:VCARD"""
                    st.download_button("📇 Download vCard", vcard, "contact.vcf", "text/vcard")
                
                with col_d3:
                    st.download_button("🖼️ Download Image", img_bytes, f"card_{next_number}.png", "image/png")
                
                # Clear processed data
                st.session_state.processed_data = {}
                st.rerun()
            else:
                st.error("❌ Failed to save contact to database")
            
        except Exception as e:
            st.error(f"❌ Error saving data: {str(e)}")

# ---------- VIEW SAVED DATA WITH DELETE OPTION ----------
st.header("📂 Saved Contacts")

# Toggle delete mode
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Contact Database")
with col2:
    if st.button("🗑️ Delete Mode" if not st.session_state.delete_mode else "✅ Exit Delete Mode"):
        st.session_state.delete_mode = not st.session_state.delete_mode
        st.rerun()

df = load_database()
if not df.empty:
    # Display dataframe without Image_Path
    display_columns = ['Name', 'Designation', 'Email', 'Phone', 'Company', 'Website', 'Address']
    
    if st.session_state.delete_mode:
        st.warning("🗑️ **Delete Mode Active** - Click on records to delete them")
        
        # Create a selectable dataframe for deletion
        for i, row in df.iterrows():
            with st.container():
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    st.write(f"**{row['Name']}** - {row['Designation']}")
                    st.write(f"📧 {row['Email']} | 📞 {row['Phone']}")
                    st.write(f"🏢 {row['Company']} | 🌐 {row['Website']}")
                    if pd.notna(row['Address']) and row['Address'] != '':
                        st.write(f"📍 {row['Address']}")
                    st.markdown("---")
                
                with col_b:
                    if st.button("Delete", key=f"delete_{i}"):
                        if delete_from_database(i):
                            st.success(f"✅ Record deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete record")
    else:
        # Normal display mode
        display_df = df[display_columns].copy()
        st.dataframe(display_df, use_container_width=True)
    
    # Statistics
    st.subheader("📊 Database Statistics")
    total = len(df)
    with_email = len(df[df['Email'].notna() & (df['Email'] != '')])
    with_phone = len(df[df['Phone'].notna() & (df['Phone'] != '')])
    with_company = len(df[df['Company'].notna() & (df['Company'] != '')])
    with_designation = len(df[df['Designation'].notna() & (df['Designation'] != '')])
    with_website = len(df[df['Website'].notna() & (df['Website'] != '')])
    with_address = len(df[df['Address'].notna() & (df['Address'] != '')])
    
    col_s1, col_s2, col_s3, col_s4, col_s5, col_s6, col_s7 = st.columns(7)
    col_s1.metric("Total", total)
    col_s2.metric("With Email", with_email)
    col_s3.metric("With Phone", with_phone)
    col_s4.metric("With Designation", with_designation)
    col_s5.metric("With Company", with_company)
    col_s6.metric("With Website", with_website)
    col_s7.metric("With Address", with_address)
    
    # Export option
    st.download_button("💾 Export Full Database", df.to_csv(index=False).encode('utf-8'), 
                     "visiting_cards_complete.csv", "text/csv")
    
else:
    st.info("No contacts saved yet. Process your first visiting card above!")

# ---------- INSTRUCTIONS ----------
with st.expander("💡 Tips for Better Recognition"):
    st.markdown("""
    **For best OCR results:**
    - Use high-quality, well-lit images
    - Ensure text is clear and not blurry
    - Position the card straight
    - Avoid shadows and glares
    
    **What gets detected automatically:**
    - **Name**: First prominent capitalized line
    - **Email**: Complete email address
    - **Website**: Domain from email (everything after @)
    - **Company**: Company name from email domain
    - **Phone**: Various national & international formats
    - **Designation**: Job titles and positions
    - **Address**: Street, building, city, pincode information
    
    **Features:**
    - Edit all fields before saving
    - Delete unwanted records
    - Export complete database
    - Download vCard for contacts
    """)