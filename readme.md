# Real-Time Process Monitoring Dashboard

A Python-based real-time process monitoring dashboard built using `Tkinter` for the GUI, `psutil` for system process management, and `matplotlib` for visualizing CPU and memory usage over time.

## Features

- **Real-Time Process Monitoring**: Displays a list of running processes with details such as PID, name, state, CPU usage, memory usage, and duration.
- **Search Functionality**: Search for processes by name.
- **Pagination**: Navigate through processes with pagination controls.
- **Terminate Processes**: Terminate selected processes directly from the dashboard.
- **Process Details**: View detailed information about a selected process, including start time, user, and thread count.
- **Graphs**: Real-time graphs for CPU and memory usage over time.
- **Dark Theme**: A visually appealing dark theme for better user experience.

## Project Structure
├── dashboard.py # Main application file ├── data_collection.py # Handles process data collection ├── data_processing.py # Processes raw data and provides utility functions ├── pycache/ # Compiled Python files (auto-generated)


## Requirements

- Python 3.8 or higher
- Required Python libraries:
  - `tkinter`
  - `psutil`
  - `pandas`
  - `matplotlib`

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/real-time-process-monitoring-dashboard.git
   cd real-time-process-monitoring-dashboard
   
2.  Install the required Python libraries:
    pip install psutil pandas matplotlib
3. Run the application:
    python dashboard.py
Usage
Launch the application by running dashboard.py.
Use the search bar to filter processes by name.
Navigate through the process list using the pagination controls.
Select a process to view details or terminate it using the respective buttons.
Monitor CPU and memory usage in real-time through the graphs.
Screenshots
Main Dashboard
<img alt="Main Dashboard" src="https://via.placeholder.com/1200x700?text=Screenshot+Placeholder">
Process Details
<img alt="Process Details" src="https://via.placeholder.com/600x400?text=Screenshot+Placeholder">
Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgments
psutil for process management.
matplotlib for data visualization.
Tkinter for the GUI framework.