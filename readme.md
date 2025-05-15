# Google Maps ETL Pipeline

This project implements a robust ETL (Extract, Transform, Load) pipeline for scraping coffee shop data from Google Maps. The pipeline is designed to automate the process of gathering, cleaning, and storing data for further analysis or application development.

## Overview

The pipeline consists of several components that work together to extract data from Google Maps, transform it into a usable format, and load it into CSV and JSON files. This allows for easy integration with other applications or data analysis tools.

## Components

- **config.py**: Contains configuration settings for the pipeline, including search queries, location settings, and options for the web driver.
  
- **extract.py**: Responsible for data extraction from Google Maps. This module uses Selenium to navigate the Google Maps interface, perform searches, and collect data about coffee shops.

- **transform.py**: Handles data cleaning and transformation. This module processes the raw data extracted from Google Maps, ensuring it is in a consistent format and ready for analysis.

- **load.py**: Manages the loading of transformed data into output files. This module saves the data in both CSV and JSON formats, making it accessible for various use cases.

- **main.py**: Orchestrates the entire ETL process. This script initializes the pipeline, calls the extraction, transformation, and loading functions, and handles logging and error management.

## Usage

1. **Install Dependencies**: Ensure you have Python and the required libraries installed. You can install the necessary packages using:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Settings**: Modify the `config.py` file to set your desired search query and location.

3. **Run the Pipeline**: Execute the `main.py` script to start the ETL process:
   ```bash
   python main.py --search-query "coffee shop" --location "Semarang, Indonesia"
   ```

4. **Output**: The results will be saved in the `output` directory as both CSV and JSON files.

## Logging

The pipeline includes logging functionality to track the progress and any issues that may arise during execution. Logs will be saved in the `logs` directory.

## Contributing

Contributions are welcome! If you have suggestions for improvements or additional features, feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.