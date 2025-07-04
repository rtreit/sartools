"""
Data utilities for processing D4H incident data.

This module provides functions for loading, cleaning, and transforming
D4H incident data from JSON format into pandas DataFrames.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime


def load_incidents_json(file_path: str) -> Dict[str, Any]:
    """
    Load incidents data from JSON file.
    
    Args:
        file_path: Path to the incidents JSON file
        
    Returns:
        Dictionary containing the loaded JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_incidents_data(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract the incidents list from the loaded JSON data.
    
    Args:
        json_data: The full JSON data structure
        
    Returns:
        List of incident dictionaries
    """
    return json_data.get('incidents', [])


def create_incidents_dataframe(incidents: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a pandas DataFrame from incidents data.
    
    Args:
        incidents: List of incident dictionaries
        
    Returns:
        Pandas DataFrame with normalized incident data
    """
    df = pd.json_normalize(incidents)
    return df


def clean_incidents_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the incidents DataFrame.
    
    Args:
        df: Raw incidents DataFrame
        
    Returns:
        Cleaned DataFrame with proper data types and formatting
    """
    df_clean = df.copy()
    
    # Convert date columns to datetime
    date_columns = ['createdAt', 'createdOrPublishedAt', 'updatedAt', 'startsAt', 'endsAt']
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Convert coordinates to numeric
    if 'location.coordinates' in df_clean.columns:
        # Extract latitude and longitude from coordinates
        coords = df_clean['location.coordinates'].apply(
            lambda x: [float(x[0]), float(x[1])] if isinstance(x, list) and len(x) == 2 else [None, None]
        )
        df_clean['latitude'] = coords.apply(lambda x: x[0])
        df_clean['longitude'] = coords.apply(lambda x: x[1])
    
    # Convert numeric columns
    numeric_columns = ['bearing', 'countAttendance', 'countGuests', 'distance', 'percAttendance']
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Clean text columns (remove HTML tags from description)
    text_columns = ['description', 'referenceDescription']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.replace(r'<[^>]+>', '', regex=True)
    
    return df_clean


def get_incident_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of the incidents data.
    
    Args:
        df: Incidents DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        'total_incidents': len(df),
        'date_range': {
            'earliest': df['startsAt'].min() if 'startsAt' in df.columns else None,
            'latest': df['startsAt'].max() if 'startsAt' in df.columns else None
        },
        'attendance_stats': {
            'mean': df['countAttendance'].mean() if 'countAttendance' in df.columns else None,
            'median': df['countAttendance'].median() if 'countAttendance' in df.columns else None,
            'max': df['countAttendance'].max() if 'countAttendance' in df.columns else None
        },
        'location_coverage': {
            'unique_towns': df['address.town'].nunique() if 'address.town' in df.columns else None,
            'unique_regions': df['address.region'].nunique() if 'address.region' in df.columns else None
        }
    }
    return summary


def load_and_process_incidents(file_path: str) -> pd.DataFrame:
    """
    Complete pipeline to load and process incidents data.
    
    Args:
        file_path: Path to the incidents JSON file
        
    Returns:
        Cleaned and processed incidents DataFrame
    """
    # Load the JSON data
    json_data = load_incidents_json(file_path)
    
    # Extract incidents
    incidents = extract_incidents_data(json_data)
    
    # Create DataFrame
    df = create_incidents_dataframe(incidents)
    
    # Clean the data
    df_clean = clean_incidents_dataframe(df)
    
    return df_clean
