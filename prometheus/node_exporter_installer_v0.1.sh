#!/bin/bash

# Default values for installation
DEFAULT_BINARY_PATH="$(pwd)/node_exporter-1.8.2.linux-amd64.tar.gz" # Default offline installation path
DEFAULT_INSTALL_DIR="/opt/monitoring/node_exporter" # Default installation directory
DEFAULT_NODE_EXPORTER_VERSION="1.8.2" 
NODE_EXPORTER_LATEST_VERSION=$(curl -s https://api.github.com/repos/prometheus/node_exporter/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
SYMLINK_PATH="/usr/local/bin/node_exporter" 
PORT=9100

# Function to handle errors and exit
function error_exit {
    echo -e "\033[1;33m[ERROR] $1\033[0m" >&2
    exit 1
}

# Function to log installation progress
function log_info {
    echo -e "\033[1;36m[INFO] $1\033[0m" 
}

function log_error {
    echo -e "\033[1;33m[ERROR] $1[0m" 
}

if [[ $(id -u) -ne 0 ]]; then
    error_exit "This script must be run as root" 
fi

function check_install_directory {
    if [[ ! -d "$INSTALL_DIR" ]] ; then
        log_info "Installation directory does not exist. Creating $INSTALL_DIR..." 
        mkdir -p "$INSTALL_DIR" || error_exit "Failed to create directory $INSTALL_DIR." 
    fi
}

function check_selinux {
    if [[ $(getenforce) == "Enforcing" ]]; then
        error_exit "SELinux is enabled. You need to disable..(e.g. setenforce 0)" 
    fi
}

function check_installation {
    if [[ -f "$SYMLINK_PATH" ]]; then
        binary=$(command -v node_exporter)
        version=$(node_exporter --version | head -1)
        error_exit "Node Exporter is already installed. ($version)" 
    fi
}

function system_information {
    echo -e "\033[1;36m-------------------------------System Information----------------------------\033[0m" 

    if [[ -f /etc/redhat-release ]] ; then
        OS_VERSION=$(cat /etc/redhat-release)
        echo -e "\033[1;36m* Operating Syttem: $OS_VERSION\033[0m" 
    elif [[ -f /etc/os-release ]]; then
        OS_NAME=$(grep '^NAME=' /etc/os-release | cut -d= -f2 | tr -d '"')
        OS_VERSION=$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
        echo -e "\033[1;36m* Operating Syttem: $OS_NAME $OS_VERSION\033[0m" 
    else
        OS_NAME=$(uname -s)
        OS_VERSION=$(uname -r)
        echo -e "\033[1;36m* Operating Syttem: $OS_NAME $OS_VERSION\033[0m" 
    fi
    echo "" 

    if ps -ef | grep 'node_exporter' | grep -v grep | grep -v installer | grep -v vi > /dev/null; then
        echo -e "\033[1;31m* Node Exporter is running...\033[0m" 
    ps -ef | grep 'node_exporter' | grep -v grep | grep -v installer | grep -v vi
    echo "" 
    else
        echo -e "\033[1;36m* Node Exporter is not running\033[0m" 
    echo "" 
    fi

    if ss -tulnp | grep ":$PORT" > /dev/null; then
        echo -e "\033[1;31m* Port 9100 is listening... \033[0m" 
        ss -tulnp | grep ":$PORT" 
        PORT=38001
        while true; do
            if ss -tulnp | grep ":$PORT" > /dev/null; then
                echo -e "\033[1;31m* Port $PORT is listening... \033[0m" 
                ss -tulnp | grep ":$PORT" 
                ((PORT+=1))
            else
                break
            fi
        done
        log_info "The port has been changed to \"$PORT\"." 
    else
        echo -e "\033[1;36m* Port 9100 is not using... \033[0m" 
    fi
    echo -e "\033[1;36m-----------------------------------------------------------------------------\033[0m" 
}

system_information

# Online installation function
function online_install {
    log_info "Starting online installation of Node Exporter..." 

    log_info "Downloading Node Exporter version: $NODE_EXPORTER_VERSION" 
    wget https://github.com/prometheus/node_exporter/releases/download/v$NODE_EXPORTER_VERSION/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz || error_exit "Download failed." 

    # Extract and install
    log_info "Extracting Node Exporter..." 
    tar -xvf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz -C $INSTALL_DIR || error_exit "Failed to extract Node Exporter." 
    cd $INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64 || error_exit "Failed to change directory." 
    sudo ln -s "$INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" "$SYMLINK_PATH"|| error_exit "Failed to create symlink at $SYMLINK_PATH." 

    # Move binary to the desired directory
    #sudo mv node_exporter "$INSTALL_DIR" || error_exit "Failed to move Node Exporter binary." 
}

# Offline installation function
function offline_install {
    [[ -z "$BINARY_PATH" ]] && error_exit "Binary path must be provided for offline installation." 

    log_info "Starting offline installation of Node Exporter..." 
    [[ ! -f "$BINARY_PATH" ]] && error_exit "File not found at $BINARY_PATH." 
    NODE_EXPORTER_VERSION=$(echo "$BINARY_PATH" | sed -E 's/.*node_exporter-([0-9\.]+)\..*/\1/')
    [[ "$BINARY_PATH" == $NODE_EXPORTER_VERSION ]] && error_exit "Failed to extract node_exporter version from filename: $BINARY_PATH" 

    log_info "Extracting Node Exporter from provided path..." 
    tar -xvf "$BINARY_PATH" -C $INSTALL_DIR || error_exit "Failed to extract Node Exporter from $BINARY_PATH." 
    #cd node_exporter-* || error_exit "Failed to change directory after extraction." 
    cd $INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64 || error_exit "Failed to change directory." 
    sudo ln -s "$INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" "$SYMLINK_PATH"|| error_exit "Failed to create symlink at $SYMLINK_PATH." 

    # Move binary to the desired directory
    #sudo mv node_exporter "$INSTALL_DIR" || error_exit "Failed to move Node Exporter binary." 
}

# Uninstall Node Exporter
function uninstall {
    log_info "Uninstalling Node Exporter..." 

    # Stop the Node Exporter service if it's running
    if systemctl is-active --quiet node_exporter; then
        sudo systemctl stop node_exporter || error_exit "Failed to stop Node Exporter service." 
    fi

    # Disable the service
    sudo systemctl disable node_exporter || log_error "Failed to disable Node Exporter service." 

    # Remove the service file
    sudo rm /etc/systemd/system/node_exporter.service || log_error "Failed to remove Node Exporter service file." 
    sudo systemctl daemon-reload || log_error "Failed to reload systemd." 

    #Remove node exporter directory
    DELETE_DIR="$INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64" 
    if [[ -f "$SYMLINK_PATH" ]]; then
    sudo rm "$SYMLINK_PATH" || error_exit "Failed to remove symlink "$SYMLINK_PATH"." 
    fi

    if [[ -d "$DELETE_DIR" ]]; then
        sudo rm -r $DELETE_DIR || error_exit "Failed to remove Node Exporter directory $INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64" 
    fi

    log_info "Node Exporter has been uninstalled successfully." 
    exit 0

}
# Configure Node Exporter as a systemd service
function configure_service {
    log_info "Configuring Node Exporter as a systemd service..." 

    sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
Environment="NODE_EXPORTER_ARGS=--web.listen-address=\":$PORT\"" 
ExecStart=$SYMLINK_PATH \$NODE_EXPORTER_ARGS

[Install]
WantedBy=multi-user.target

EOF

    log_info "Enabling and starting Node Exporter service..." 
    sudo systemctl daemon-reload || error_exit "Failed to reload systemd." 
    sudo systemctl enable node_exporter || error_exit "Failed to enable Node Exporter service." 
    sudo systemctl start node_exporter || error_exit "Failed to start Node Exporter service." 

    log_info "Node Exporter installation and configuration completed." 
}

# Handle installation mode selection
while true; do
    case "$INSTALL_MODE_INPUT" in
        1)
            INSTALL_MODE="online" 
            read -p "Enter the Node Exporter version to install (default: $DEFAULT_NODE_EXPORTER_VERSION / latest: $NODE_EXPORTER_LATEST_VERSION): " NODE_EXPORTER_VERSION
            NODE_EXPORTER_VERSION=${NODE_EXPORTER_VERSION:-$DEFAULT_NODE_EXPORTER_VERSION}
        break
            ;;
        2)
            INSTALL_MODE="offline" 
            # Ask for the binary path if offline, use default if not provided
            read -p "Enter the path to the installation file (default: $DEFAULT_BINARY_PATH): " BINARY_PATH
            BINARY_PATH=${BINARY_PATH:-$DEFAULT_BINARY_PATH}
        break
            ;;
        3)
            INSTALL_MODE="uninstall" 
        break
            ;;
        4)
        exit 0
            ;;
        *)
        echo "Choose installation method: " 
        echo "1. Online install" 
        echo "2. Offline install" 
        echo "3. Uninstall" 
        echo "4. exit" 
        read -p "Enter your choice (1/2/3/4): " INSTALL_MODE_INPUT
            #error_exit "Invalid choice. Please choose 1 or 2." 
            ;;
    esac
done

if [[ "$INSTALL_MODE" == "uninstall" ]]; then
    NODE_EXPORTER_VERSION=${BINARY_PATH:-$DEFAULT_NODE_EXPORTER_VERSION}
    read -p "Enter the uninstallation directory (default: $DEFAULT_INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64): " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}

    read -p "Proceed with the uninstallation? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
        echo "Uninstallation aborted." 
        exit 0
    fi
else
    # Ask for installation directory, use default if not provided
    read -p "Enter the installation directory (default: $DEFAULT_INSTALL_DIR): " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}

    # Print installation settings
    echo "-----------------------------------------------------------------------------------------" 
    echo "Installation mode: $INSTALL_MODE" 
    if [[ "$INSTALL_MODE" == "offline" ]]; then
        echo "Installation file path: $BINARY_PATH" 
    fi
    echo "Installation directory: $INSTALL_DIR" 

    # Confirm to proceed with installation
    read -p "Proceed with the installation? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
        echo "Installation aborted." 
        exit 0
    fi

    # Branching for online or offline installation

fi

# Branching for online or offline installation
case "$INSTALL_MODE" in
    online)
        check_installation
        check_selinux
        check_install_directory
        online_install
        ;;
    offline)
        check_installation
        check_selinux
        check_install_directory
        offline_install
        ;;
    uninstall)
        uninstall
        ;;
    *)
        error_exit "Invalid installation mode." 
        ;;
esac

# Configure Node Exporter service
configure_service

log_info "Installation finished successfully." 
