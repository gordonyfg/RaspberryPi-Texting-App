# Texting App for Raspberry Pi

## Introduction

This project is a messaging application developed using the Kivy framework. It supports multiple communication protocols and implements a client-server architecture, allowing for local network communication simulation.

## Features

- **Multi-Protocol Support**: 
  - Ethernet (TCP/IP) with Master/Client modes
  - UART (Serial) communication support
  - Extensible protocol handler system

- **Modern UI Features**:
  - Dark theme interface
  - WhatsApp-style message bubbles
  - Real-time message updates
  - Protocol selection sidebar
  - Automatic scrolling to latest messages

- **Networking Features**:
  - TCP/IP socket communication
  - Client-Server architecture
  - Connection state management
  - Error handling and recovery

- **Data Persistence**:
  - SQLite database for message history
  - Protocol-specific message filtering
  - REST API for database operations

## Technical Stack

- **Frontend**: Kivy Framework
- **Backend**: 
  - Python 3.x
  - Flask REST API
  - SQLite Database
- **Protocols**:
  - TCP/IP (Ethernet)
  - UART (Serial)

## Requirements

- Python 3.x
- Kivy
- Flask
- SQLite3
- Required Python packages:
  ```
  kivy
  flask
  requests
  sqlite3
  ```

## Setup

1. Clone the repository
2. Install dependencies
3. Run tests and save results:
   ```bash
   pytest -v --cov=. --cov-report=term-missing | tee test_results.txt
   ```
4. Run the application:
   ```bash
   python chatapp.py
   ```

## Configuration

The application automatically finds available ports for:
- REST API server (starting from port 5000)
- Protocol communication (using next available port)
If default ports are in use, the app will automatically find and use free ports.

## Usage

1. Start the application
2. Select a protocol:
   - Ethernet(Master): Acts as server
   - Ethernet(Client): Connects to a master
   - UART: For serial communication
3. Messages will appear in real-time
4. Connection status is shown in system messages

## Architecture

- **Modular Protocol System**: Extensible protocol handlers
- **MVC-like Structure**: Separation of UI, logic, and data
- **Event-Driven**: Real-time message handling
- **REST API**: Database operations via HTTP endpoints