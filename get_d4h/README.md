# get-d4h

A Python tool for extracting incident data from D4H (Incident Management Platform) for Search and Rescue teams.

## Overview

This project is part of the **sartools** suite and provides automated data extraction capabilities for D4H Team Manager, specifically designed for Search and Rescue (SAR) operations. It uses browser automation to authenticate with D4H and then leverages the D4H API to bulk export incident data for analysis, reporting, and archival purposes.

## Features

- **Automated Authentication**: Uses Playwright to handle D4H login flow
- **Bulk Data Export**: Retrieves incident data across configurable date ranges (2018-2026+ supported)
- **Optimized Pagination**: Automatically determines optimal page sizes for efficient data retrieval
- **Comprehensive Data Collection**: Extracts complete incident records including:
  - Incident details (description, dates, location coordinates)
  - Attendance and participation metrics
  - Weather conditions
  - Custom field values
  - Approval status and tracking information
- **Structured Output**: Saves data in JSON format with metadata for easy processing
- **Error Handling**: Robust error handling and retry logic for reliable data extraction

## Prerequisites

- Python 3.11 or higher
- Access to a D4H Team Manager instance
- Valid D4H user credentials with incident viewing permissions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rtreit/sartools.git
cd sartools/get_d4h
```

2. Install dependencies:
```bash
uv sync
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Basic Usage

Run the main script:
```bash
python main.py
```

### Interactive Process

1. **Browser Launch**: The script will open a Chromium browser window
2. **Manual Login**: You'll need to manually sign in to your D4H account when prompted
3. **Data Collection**: Once authenticated, the script will automatically:
   - Test optimal page sizes for data retrieval
   - Collect all incidents within the specified date range
   - Display progress and statistics during collection
4. **Output**: Results are saved to `incidents.json`

### Configuration

The script is pre-configured for Santa Clara Valley SAR (`scvsar.team-manager.us.d4h.com`), but can be modified for other D4H instances by updating the `API_URL` variable in `main.py`.

**Date Range**: Currently set to collect incidents from 2018-01-01 to 2026-12-31. Modify the date parameters in the code to adjust this range.

## Output Format

The script generates a `incidents.json` file with the following structure:

```json
{
  "metadata": {
    "total_incidents": 920,
    "date_range": {
      "start": "2018-01-01T00:00:00.000Z",
      "end": "2026-12-31T00:00:00.000Z"
    },
    "collected_at": "2025-07-02T00:00:00.000Z",
    "page_size_used": 1000,
    "pages_fetched": 1
  },
  "incidents": [
    // Array of incident objects with full D4H data structure
  ]
}
```

Each incident record includes:
- Basic incident information (ID, description, dates)
- Geographic data (coordinates, bearing, distance)
- Participation metrics (attendance count, percentages)
- Operational details (coordinator, weather, approval status)
- Custom field values specific to your D4H configuration

## Technical Details

### Architecture

- **Browser Automation**: Uses Playwright for reliable authentication and session management
- **API Integration**: Leverages D4H's internal API for efficient bulk data retrieval
- **Request Interception**: Captures authentication headers and session cookies from browser interactions
- **Adaptive Pagination**: Tests multiple page sizes to optimize data retrieval performance

### Performance

- Supports page sizes up to 1000 incidents per request
- Automatic retry logic for failed requests
- Progress tracking and detailed logging
- Efficient memory usage for large datasets

### Security

- Uses browser-based authentication (no stored credentials)
- Session cookies are captured securely during browser interaction
- Headers and authentication tokens are handled in-memory only

## Dependencies

- **playwright**: Browser automation for authentication
- **requests**: HTTP client for API interactions
- **json**: JSON data processing (built-in)

## Use Cases

This tool is particularly useful for:

- **Data Analysis**: Export historical incident data for trend analysis
- **Reporting**: Generate custom reports from D4H data
- **Backup/Archival**: Create local backups of incident records
- **Integration**: Feed D4H data into other analysis tools or dashboards
- **Migration**: Extract data for system migrations or consolidation

## Limitations

- Requires manual authentication (cannot be fully automated due to D4H security)
- Limited to incidents within the specified date range
- Dependent on D4H API structure (may require updates if D4H changes their API)
- Browser must remain open during the authentication phase

## Troubleshooting

### Common Issues

1. **Authentication Failures**: Ensure you're logged into the correct D4H instance and have appropriate permissions
2. **Empty Results**: Check date ranges and verify incidents exist in the specified timeframe
3. **API Errors**: May indicate changes to D4H's API structure or authentication requirements

### Debug Mode

The browser launches in non-headless mode by default for easier debugging. Monitor the console output for detailed progress information and error messages.

## Contributing

This tool is part of the larger sartools project. Contributions and improvements are welcome, particularly for:

- Supporting additional D4H instances
- Enhanced error handling and recovery
- Additional data export formats
- Performance optimizations

## License

[Include your license information here]

## Support

For issues specific to this tool, please check the existing incident data and ensure your D4H credentials and permissions are correct. For broader sartools questions, refer to the main project repository.

---

*Part of the sartools suite for Search and Rescue operations*