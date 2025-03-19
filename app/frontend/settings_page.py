import streamlit as st
import logging
import json
import os
from datetime import datetime

from app.utils.session import get_current_user
from app.utils.auth import get_password_hash
from app.database.user_repository import UserRepository
from app.database.conversation_repository import ConversationRepository
from app.config.config import DEFAULT_CATEGORIES, EXPORT_DIR

# Configure logging
logger = logging.getLogger(__name__)

def show_settings():
    """Display user settings and application configuration options"""
    try:
        st.title("Settings")
        
        # Get current user
        user = get_current_user()
        if not user:
            st.warning("User session expired. Please log in again.")
            return
        
        # Initialize repositories
        user_repo = UserRepository()
        conversation_repo = ConversationRepository()
        
        # Create tabs for different settings
        tab1, tab2, tab3, tab4 = st.tabs([
            "Profile", "Categories & Tags", "Import/Export", "Developer"
        ])
        
        # Tab 1: Profile Settings
        with tab1:
            st.subheader("User Profile")
            
            # Current profile info
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Name:** {user['name']}")
            
            # Form to change name
            with st.form("update_name_form"):
                st.subheader("Update Profile Name")
                new_name = st.text_input("New Name", value=user['name'])
                submit_name = st.form_submit_button("Update Name")
                
                if submit_name:
                    if not new_name or new_name == user['name']:
                        st.warning("Please enter a new name.")
                    else:
                        try:
                            # Update user name
                            user_repo.update(user['id'], {"name": new_name})
                            st.success("Name updated successfully!")
                            # Update session state
                            st.session_state.user_name = new_name
                        except Exception as e:
                            logger.error(f"Error updating name: {e}")
                            st.error(f"Error updating name: {str(e)}")
            
            # Form to change password
            with st.form("update_password_form"):
                st.subheader("Change Password")
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submit_password = st.form_submit_button("Update Password")
                
                if submit_password:
                    if not current_password or not new_password or not confirm_password:
                        st.warning("Please fill out all password fields.")
                    elif new_password != confirm_password:
                        st.error("New passwords do not match.")
                    elif len(new_password) < 8:
                        st.error("Password should be at least 8 characters long.")
                    else:
                        try:
                            # Verify current password
                            from app.utils.auth import verify_password
                            
                            # Get user with hashed password
                            full_user = user_repo.get_by_id(user['id'])
                            
                            if not verify_password(current_password, full_user.hashed_password):
                                st.error("Current password is incorrect.")
                            else:
                                # Hash new password
                                hashed_password = get_password_hash(new_password)
                                
                                # Update user
                                user_repo.update(user['id'], {"hashed_password": hashed_password})
                                st.success("Password updated successfully!")
                        except Exception as e:
                            logger.error(f"Error updating password: {e}")
                            st.error(f"Error updating password: {str(e)}")
        
        # Tab 2: Categories & Tags
        with tab2:
            st.subheader("Manage Categories and Tags")
            
            # Get existing categories and tags
            all_categories = conversation_repo.get_all_categories(user['id'])
            all_tags = conversation_repo.get_all_tags(user['id'])
            
            # Custom categories
            st.write("**Custom Categories**")
            
            # Current custom categories
            st.write("Your current custom categories:")
            custom_categories = user.get('custom_categories', [])
            
            if custom_categories:
                category_html = " ".join([f'<span class="category">{cat}</span>' for cat in custom_categories])
                st.markdown(category_html, unsafe_allow_html=True)
            else:
                st.write("No custom categories defined.")
            
            # Form to add custom category
            with st.form("add_category_form"):
                st.subheader("Add New Category")
                
                # Suggest categories from default list
                suggested_categories = [cat for cat in DEFAULT_CATEGORIES if cat not in custom_categories]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_category = st.text_input("New Category Name")
                
                with col2:
                    if suggested_categories:
                        selected_suggestion = st.selectbox(
                            "Or select from suggestions:", 
                            [""] + suggested_categories
                        )
                
                submit_category = st.form_submit_button("Add Category")
                
                if submit_category:
                    # Determine which category to add
                    category_to_add = selected_suggestion if selected_suggestion else new_category
                    
                    if not category_to_add:
                        st.warning("Please enter a category name or select from suggestions.")
                    else:
                        try:
                            # Update user's custom categories
                            updated_categories = custom_categories + [category_to_add]
                            user_repo.update_preferences(user['id'], {"custom_categories": updated_categories})
                            st.success(f"Added category: {category_to_add}")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error adding category: {e}")
                            st.error(f"Error adding category: {str(e)}")
            
            # Favorite tags
            st.write("**Favorite Tags**")
            favorite_tags = user.get('favorite_tags', [])
            
            if favorite_tags:
                tag_html = " ".join([f'<span class="tag">{tag}</span>' for tag in favorite_tags])
                st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.write("No favorite tags defined.")
            
            # Existing tags in conversations
            if all_tags:
                st.write("Tags used in your conversations:")
                available_tags = [tag for tag in all_tags if tag not in favorite_tags]
                
                if available_tags:
                    tags_html = " ".join([f'<span class="tag">{tag}</span>' for tag in available_tags[:20]])
                    st.markdown(tags_html, unsafe_allow_html=True)
            
            # Form to add favorite tag
            with st.form("add_tag_form"):
                new_tag = st.text_input("Add a Favorite Tag")
                submit_tag = st.form_submit_button("Add Tag")
                
                if submit_tag:
                    if not new_tag:
                        st.warning("Please enter a tag name.")
                    else:
                        try:
                            # Update user's favorite tags
                            updated_tags = favorite_tags + [new_tag]
                            user_repo.update_preferences(user['id'], {"favorite_tags": updated_tags})
                            st.success(f"Added tag: {new_tag}")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error adding tag: {e}")
                            st.error(f"Error adding tag: {str(e)}")
        
        # Tab 3: Import/Export
        with tab3:
            st.subheader("Import & Export")
            
            # Import from ChatGPT
            st.write("**Import from ChatGPT**")
            st.write("Upload your ChatGPT conversation history to import it into this system.")
            
            uploaded_file = st.file_uploader("Upload ChatGPT conversation JSON", type=["json"])
            
            if uploaded_file:
                st.write("File uploaded successfully. Review the data before importing.")
                try:
                    # Read the file
                    chat_data = json.load(uploaded_file)
                    
                    # Display summary
                    if isinstance(chat_data, list):
                        st.write(f"Found {len(chat_data)} conversations to import.")
                        
                        if st.button("Import Conversations"):
                            # Use optimized import for large files
                            from app.utils.optimized_import import chunked_import
                            
                            # Convert to string for import
                            file_content = uploaded_file.getvalue().decode('utf-8')
                            
                            # Set up progress tracking
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Define progress callback
                            def update_progress(count):
                                # We don't know the total, so estimate based on file size
                                estimated_total = len(chat_data)
                                if estimated_total > 0:
                                    progress = min(1.0, count / estimated_total)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Processed {count} of ~{estimated_total} conversations...")
                            
                            with st.spinner("Importing conversations..."):
                                # Import with chunking
                                results = chunked_import(
                                    file_content, 
                                    user['id'], 
                                    chunk_size=20,  # Process 20 conversations at a time
                                    callback=update_progress
                                )
                                
                                # Complete the progress bar
                                progress_bar.progress(1.0)
                                
                                # Show results
                                st.success(f"Import complete! Successfully imported {results['success']} conversations.")
                                if results['error'] > 0:
                                    st.warning(f"{results['error']} conversations could not be imported.")
                                
                                # Show import stats
                                if 'duration_seconds' in results:
                                    duration_mins = results['duration_seconds'] / 60
                                    st.info(f"Import took {duration_mins:.1f} minutes to process {results['total_processed']} conversations.")
                    else:
                        st.error("Invalid format. Expected a list of conversations.")
                except Exception as e:
                    logger.error(f"Error processing import file: {e}")
                    st.error(f"Error processing file: {str(e)}")
            
            # Export functionality
            st.write("**Export Your Data**")
            st.write("Export your conversations data for backup or moving to another system.")
            
            # Get export options
            export_format = st.selectbox(
                "Export Format", 
                ["JSON", "CSV", "Plain Text"]
            )
            
            if st.button("Export All Conversations"):
                try:
                    # Get all user conversations
                    conversations = conversation_repo.get_by_user(user["id"])
                    
                    if not conversations:
                        st.warning("You don't have any conversations to export.")
                    else:
                        # Create export filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{user['email'].split('@')[0]}_export_{timestamp}"
                        
                        if export_format == "JSON":
                            # Convert to dict
                            export_data = [conv.to_dict() for conv in conversations]
                            for conv_dict in export_data:
                                # Convert dates to strings for JSON serialization
                                conv_dict['created_at'] = conv_dict['created_at'].isoformat()
                                conv_dict['updated_at'] = conv_dict['updated_at'].isoformat()
                                
                                # Convert message dates
                                for msg in conv_dict['messages']:
                                    msg['timestamp'] = msg['timestamp'].isoformat()
                            
                            # Save as JSON file
                            filepath = os.path.join(EXPORT_DIR, f"{filename}.json")
                            with open(filepath, 'w') as f:
                                json.dump(export_data, f, indent=2)
                            
                            st.success(f"Export successful! File saved to: {filepath}")
                        
                        elif export_format == "CSV":
                            st.info("CSV export will be implemented in the next version.")
                        
                        elif export_format == "Plain Text":
                            st.info("Plain text export will be implemented in the next version.")
                        
                except Exception as e:
                    logger.error(f"Error exporting data: {e}")
                    st.error(f"Error exporting data: {str(e)}")
        
        # Tab 4: Developer Settings
        with tab4:
            st.subheader("Developer Settings")
            
            st.write("**Application Information**")
            
            # Display app information
            from app.config.config import APP_NAME, EMBEDDING_MODEL, GPT_MODEL
            
            st.write(f"Application: {APP_NAME}")
            st.write(f"Embedding Model: {EMBEDDING_MODEL}")
            st.write(f"GPT Model: {GPT_MODEL}")
            
            # Display database stats
            st.write("**Database Statistics**")
            
            # Count of conversations
            conversation_count = len(conversation_repo.get_by_user(user['id']))
            st.write(f"Total Conversations: {conversation_count}")
            
            # Count of embeddings
            from app.database.embedding_repository import EmbeddingRepository
            embedding_repo = EmbeddingRepository()
            
            try:
                embedding_count = embedding_repo.get_embedding_count()
                st.write(f"Total Embeddings: {embedding_count}")
            except Exception:
                st.write("Embeddings: Unable to retrieve count")
            
            # System performance
            st.write("**System Performance**")
            st.info("Performance monitoring will be implemented in the next version.")
    
    except Exception as e:
        logger.error(f"Error displaying settings: {e}")
        st.error(f"An error occurred: {str(e)}")