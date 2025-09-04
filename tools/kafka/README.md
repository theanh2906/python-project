# Kafka Tool - Professional Kafka Management for Windows

A comprehensive desktop application for managing Apache Kafka on Windows, providing an intuitive GUI for server operations, topic management, consumer group administration, and real-time message simulation.

## 🚀 Features

### Core Functionality
- **Server Management**: Start/stop Kafka servers with validation and status monitoring
- **Topics Management**: Create, delete, and list Kafka topics with custom parameters
- **Consumer Groups**: Manage consumer groups with creation and deletion capabilities
- **Producer/Consumer Simulator**: Real-time message production and consumption testing
- **Real-time Console**: Live log display with filtering and search capabilities
- **Configuration Management**: View, validate, and backup Kafka configurations

### Advanced Features
- **Dual Mode Support**: Compatible with both Zookeeper and KRaft-based Kafka setups
- **Real-time Updates**: Live status monitoring and automatic data refresh
- **Professional UI**: Modern, responsive interface with tabbed navigation
- **Comprehensive Logging**: Detailed logging with export and filtering options
- **Configuration Validation**: Built-in validation for Kafka settings
- **Backup & Export**: Configuration backup and log export capabilities
- **Threading Support**: Non-blocking operations to maintain UI responsiveness

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.10 or higher
- **Apache Kafka**: 3.5.0+ (Zookeeper) or 3.7.0+ (KRaft)

### Python Dependencies
- `confluent-kafka>=2.3.0` - Core Kafka operations
- `tkinter` - GUI framework (included with Python)
- Optional: `ttkbootstrap` or `customtkinter` for enhanced UI themes

## 🛠️ Installation

### 1. Clone or Download
```bash
# If using git
git clone <repository-url>
cd kafka-tool

# Or download and extract the ZIP file
```

### 2. Install Dependencies
```bash
# Install required dependencies
pip install -r requirements.txt

# For enhanced UI (optional)
pip install ttkbootstrap

# For development (optional)
pip install pytest pytest-cov black flake8
```

### 3. Verify Installation
```bash
# Test the installation
python app/main.py
```

## 🚀 Quick Start

### 1. Launch the Application
```bash
cd tools/kafka
python app/main.py
```

### 2. Configure Kafka
1. Click **"Browse"** in the Server Control panel
2. Select your Kafka installation directory (e.g., `C:\kafka_2.13-3.7.0`)
3. The application will validate the installation and detect the Kafka mode

### 3. Start Kafka Server
1. Click **"Start Server"** to launch Kafka
2. Monitor the status in the Server Control panel
3. Check the Console Logs for detailed startup information

### 4. Manage Topics
1. Navigate to the **"Topics Management"** tab
2. Click **"Refresh Topics"** to load existing topics
3. Create new topics using the form on the right
4. Select and delete topics as needed

### 5. Test with Simulator
1. Go to the **"Producer/Consumer"** tab
2. Select a topic and consumer group
3. Send test messages or start auto-generation
4. Start a consumer to see real-time message consumption

## 📁 Project Structure

```
kafka-tool/
├── app/                          # Main application code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Application entry point
│   ├── kafka_manager.py         # Kafka server and admin operations
│   ├── producer_consumer.py     # Message simulation logic
│   ├── config_parser.py         # Configuration file handling
│   ├── logger.py                # Custom logging setup
│   └── ui/                      # User interface modules
│       ├── __init__.py
│       ├── main_window.py       # Main application window
│       ├── server_panel.py      # Server control interface
│       ├── topics_panel.py      # Topics management interface
│       ├── groups_panel.py      # Consumer groups interface
│       ├── simulator_panel.py   # Producer/consumer simulator
│       ├── console_panel.py     # Real-time log display
│       └── config_panel.py      # Configuration viewer
├── assets/                      # Application assets
│   ├── icons/                   # UI icons
│   └── themes/                  # Custom themes
├── logs/                        # Application logs
├── config/                      # Application configuration
├── tests/                       # Unit tests
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🎯 Usage Guide

### Server Management
1. **Select Kafka Folder**: Use the browse button to select your Kafka installation
2. **Validate Installation**: The tool automatically validates required files
3. **Start/Stop Server**: Use the control buttons to manage the Kafka server
4. **Monitor Status**: Real-time status updates in the interface

### Topics Operations
- **List Topics**: Automatically refreshed when server is running
- **Create Topic**: Specify name, partitions, and replication factor
- **Delete Topic**: Select from list and confirm deletion
- **Topic Details**: View basic information about selected topics

### Consumer Groups
- **List Groups**: View all active consumer groups
- **Create Group**: Groups are created automatically when consumers join
- **Delete Group**: Remove consumer groups and their offsets
- **Group Details**: View consumer group information

### Producer/Consumer Testing
- **Manual Messages**: Send individual messages to topics
- **Auto-Generation**: Automatically generate test messages at intervals
- **Real-time Consumption**: Subscribe to topics and view incoming messages
- **Message History**: Track all sent and received messages

### Configuration Management
- **View Config**: Display formatted server.properties content
- **Validate Settings**: Check configuration for common issues
- **Backup Config**: Create timestamped backups
- **Export Config**: Save configuration to external files

### Console Monitoring
- **Real-time Logs**: Live display of application and Kafka logs
- **Log Filtering**: Filter by log level (DEBUG, INFO, WARNING, ERROR)
- **Search Logs**: Find specific entries in the log history
- **Export Logs**: Save log history to files

## 🔧 Configuration

### Application Settings
The application stores settings in `config/app_config.ini`:
- Recent Kafka folders
- UI preferences
- Log levels
- Theme settings

### Kafka Configuration
The tool reads and validates your Kafka `server.properties` file:
- Automatic mode detection (Zookeeper vs KRaft)
- Configuration validation
- Bootstrap server extraction
- Setting recommendations

## 🐛 Troubleshooting

### Common Issues

**"Kafka folder validation failed"**
- Ensure you selected the correct Kafka installation directory
- Check that `bin/windows/kafka-server-start.bat` exists
- Verify `config/server.properties` is present

**"Failed to start Kafka server"**
- Check if another Kafka instance is running
- Verify Java is installed and in PATH
- Review console logs for detailed error messages

**"Admin client not initialized"**
- Ensure Kafka server is running
- Check bootstrap server configuration
- Verify network connectivity

**"Import errors on startup"**
- Install required dependencies: `pip install -r requirements.txt`
- Ensure Python 3.10+ is installed
- Check that confluent-kafka is properly installed

### Log Files
- Application logs: `logs/kafka_tool.log`
- Rotated logs: `logs/kafka_tool.log.1`, `logs/kafka_tool.log.2`, etc.
- Export logs via the Console panel for support

## 🧪 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Code Formatting
```bash
# Install formatting tools
pip install black flake8

# Format code
black app/

# Check code style
flake8 app/
```

### Building Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build standalone executable
pyinstaller --onefile --windowed app/main.py
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Check the troubleshooting section above
- Review application logs in the Console panel
- Create an issue in the repository

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Complete Kafka server management
- Topics and consumer groups administration
- Producer/consumer simulation
- Real-time logging and monitoring
- Configuration management
- Professional GUI with tabbed interface

## 🎯 Roadmap

### Planned Features
- **Cluster Management**: Support for multiple Kafka clusters
- **Message Inspector**: Advanced message viewing and analysis
- **Monitoring Dashboard**: Cluster health and performance metrics
- **Configuration Editor**: In-app editing of server.properties
- **Theme Support**: Light/dark mode toggle
- **Auto-Update**: Automatic application updates
- **Advanced Metrics**: JMX integration for detailed monitoring

### Future Enhancements
- Schema Registry integration
- Kafka Connect management
- KSQL query interface
- Message serialization support
- Performance benchmarking tools
- Cluster backup and restore

---

**Kafka Tool** - Making Kafka management simple and professional on Windows.