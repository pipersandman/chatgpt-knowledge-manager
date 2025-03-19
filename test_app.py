import streamlit as st

st.title("Test Application")
st.write("This is a simple test to verify Streamlit is working")

# Try to import your modules
try:
    # Import one module to test
    from app.utils.session import init_session_state
    st.success("Successfully imported app.utils.session")
except Exception as e:
    st.error(f"Import error: {str(e)}")