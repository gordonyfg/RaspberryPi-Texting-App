# Texting App for Raspberry Pi

## Introduction

This project is a texting application developed using the Kivy framework, designed to run on a Raspberry Pi 3B+. The application simulates inter-device communication by implementing a client-server architecture on a single device. This setup allows for the demonstration of networking concepts and communication protocols without the need for multiple physical devices.

## Features

- **Real-time Texting Simulation**: Communicate between two simulated clients on the same Raspberry Pi.
- **User-Friendly GUI**: Intuitive graphical interface developed with Kivy.
- **Client-Server Architecture**: Implements networking concepts using sockets over the localhost interface.
- **Modular Design**: Communication components are modularized for future integration with SPI/I2C protocols or multiple devices.
- **Unit and Integration Tests**: Comprehensive tests to ensure code reliability and correctness.
- **Optional Cloud Integration**: Potential to integrate with a cloud-based microservice for remote communication.

## Getting Started

### Prerequisites

- **Hardware**: Raspberry Pi 3B+
- **Operating System**: Raspberry Pi OS (32-bit)
- **Python Version**: Python 3.9 installed via Miniforge
- **Dependencies**:
  - Kivy framework
  - Additional Python packages (listed in `environment.yml`)
- **Development Tools**:
  - Git for version control

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/TextingApp-RaspberryPi.git