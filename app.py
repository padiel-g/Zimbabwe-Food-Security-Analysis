import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Zimbabwe Food Security Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and preprocess data
@st.cache_data
def load_data():
    # Read the CSV file
    df = pd.read_csv('suite-of-food-security-indicators_zwe.csv', comment='#')
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('#', '')
    
    # Convert year to proper format
    df['year'] = df['year'].astype(str).str[:4].astype(int)
    
    # Convert value to numeric, handling errors
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    return df

df = load_data()

# Sidebar
st.sidebar.title("🌾 Zimbabwe Food Security Dashboard")
st.sidebar.markdown("Explore key food security indicators for Zimbabwe from 2000-2024")

# Indicator selection
indicators = df['item'].unique()
selected_indicator = st.sidebar.selectbox("Select Indicator", indicators)

# Year range selection
min_year = int(df['year'].min())
max_year = int(df['year'].max())
year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Filter data based on selections
filtered_df = df[
    (df['item'] == selected_indicator) & 
    (df['year'] >= year_range[0]) & 
    (df['year'] <= year_range[1])
].sort_values('year')

# Main content
st.title(f"Zimbabwe Food Security Analysis: {selected_indicator}")

# Key metrics
col1, col2, col3 = st.columns(3)

with col1:
    latest_value = filtered_df['value'].iloc[-1] if not filtered_df.empty else "N/A"
    st.metric("Latest Value", f"{latest_value} {filtered_df['unit'].iloc[0] if not filtered_df.empty else ''}")

with col2:
    if len(filtered_df) > 1:
        change = ((filtered_df['value'].iloc[-1] - filtered_df['value'].iloc[0]) / filtered_df['value'].iloc[0]) * 100
        st.metric("Change Over Period", f"{change:.1f}%")
    else:
        st.metric("Change Over Period", "N/A")

with col3:
    st.metric("Years of Data", f"{len(filtered_df)} years")

# Visualization
st.subheader("Trend Over Time")

if not filtered_df.empty:
    fig = px.line(
        filtered_df, 
        x='year', 
        y='value',
        title=f"{selected_indicator} ({filtered_df['unit'].iloc[0]})",
        labels={'value': 'Value', 'year': 'Year'}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available for the selected indicator and year range.")

# Additional analysis based on indicator category
st.subheader("Indicator Analysis")

# Categorize indicators for specialized visualizations
if "undernourishment" in selected_indicator.lower():
    st.info("This indicator measures food deprivation. Lower values indicate improvement in food security.")
    
    # Compare with dietary energy supply if available
    energy_df = df[df['item'].str.contains("dietary energy supply", case=False)]
    if not energy_df.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add undernourishment trace
        fig.add_trace(
            go.Scatter(x=filtered_df['year'], y=filtered_df['value'], name=selected_indicator),
            secondary_y=False,
        )
        
        # Add dietary energy trace
        energy_filtered = energy_df[energy_df['year'].isin(filtered_df['year'])]
        fig.add_trace(
            go.Scatter(x=energy_filtered['year'], y=energy_filtered['value'], name="Dietary Energy Supply"),
            secondary_y=True,
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text=selected_indicator, secondary_y=False)
        fig.update_yaxes(title_text="Dietary Energy Supply (kcal/cap/d)", secondary_y=True)
        
        fig.update_layout(title_text="Undernourishment vs. Dietary Energy Supply")
        st.plotly_chart(fig, use_container_width=True)

elif "dietary energy" in selected_indicator.lower():
    st.info("This indicator measures the amount of food available per person. Higher values generally indicate better food security.")
    
    # Compare with GDP if available
    gdp_df = df[df['item'].str.contains("gross domestic product", case=False)]
    if not gdp_df.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add dietary energy trace
        fig.add_trace(
            go.Scatter(x=filtered_df['year'], y=filtered_df['value'], name=selected_indicator),
            secondary_y=False,
        )
        
        # Add GDP trace
        gdp_filtered = gdp_df[gdp_df['year'].isin(filtered_df['year'])]
        fig.add_trace(
            go.Scatter(x=gdp_filtered['year'], y=gdp_filtered['value'], name="GDP per capita"),
            secondary_y=True,
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text=selected_indicator, secondary_y=False)
        fig.update_yaxes(title_text="GDP per capita (Int$)", secondary_y=True)
        
        fig.update_layout(title_text="Dietary Energy Supply vs. Economic Development")
        st.plotly_chart(fig, use_container_width=True)

elif "children" in selected_indicator.lower():
    st.info("This indicator measures child nutrition status, which is a critical aspect of food security.")
    
    # Show related child nutrition indicators
    child_indicators = df[df['item'].str.contains("children", case=False)]['item'].unique()
    if len(child_indicators) > 1:
        selected_child_indicators = st.multiselect(
            "Compare with other child nutrition indicators",
            child_indicators,
            default=[selected_indicator]
        )
        
        if selected_child_indicators:
            child_df = df[
                (df['item'].isin(selected_child_indicators)) & 
                (df['year'] >= year_range[0]) & 
                (df['year'] <= year_range[1])
            ]
            
            if not child_df.empty:
                fig = px.line(
                    child_df, 
                    x='year', 
                    y='value',
                    color='item',
                    title="Child Nutrition Indicators Comparison",
                    labels={'value': 'Value', 'year': 'Year'}
                )
                st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("Raw Data")
st.dataframe(filtered_df[['year', 'value', 'unit', 'flag', 'note']].reset_index(drop=True))

# Footer
st.markdown("---")
st.markdown("**Data Source**: FAO Suite of Food Security Indicators")
st.markdown("**Note**: Data marked with 'E' are estimated, with 'X' indicating official figures")