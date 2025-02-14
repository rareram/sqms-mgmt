#!/bin/bash

# Default values for installation
DEFAULT_BINARY_PATH="$(pwd)/node_exporter-1.8.2.linux-amd64.tar.gz"   # Default offline installation path
DEFAULT_INSTALL_DIR="/opt/monitoring/node_exporter"                   # Default installation directory
DEFAULT_NODE_EXPORTER_VERSION="1.8.2"
NODE_EXPORTER_LATEST_VERSION=$(curl -s https://api.github.com/repos/prometheus/node_exporter/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
SYMLINK_PATH="/usr/local/bin/node_exporter"
PORT=9100
INIT_SYSTEM=""

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

# Enhanced system information detection
function detect_init_system {
    if command -v systemctl >/dev/null 2>&1; then
        INIT_SYSTEM="systemd"
    elif [[ -f /etc/init.d ]]; then
        INIT_SYSTEM="sysvinit"
    else
        error_exit "Unable to detect init system"
    fi
}

# Installation check functions
function check_install_directory {
    if [[ ! -d "$INSTALL_DIR" ]] ; then
        log_info "Installation directory does not exist. Creating $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR" || error_exit "Failed to create directory $INSTALL_DIR."
    fi
}

function check_selinux {
    if command -v getenforce >/dev/null 2>&1; then
        if [[ $(getenforce) == "Enforcing" ]]; then
            error_exit "SELinux is enabled. You need to disable..(e.g. setenforce 0)"
        fi
    fi
}

function check_installation {
    if [[ -f "$SYMLINK_PATH" ]]; then
        binary=$(command -v node_exporter)
        version=$(node_exporter --version | head -1)
        error_exit "Node Exporter is already installed. ($version)"
    fi
}

# Online installation function
function online_install {
    log_info "Starting online installation of Node Exporter..."

    log_info "Downloading Node Exporter version: $NODE_EXPORTER_VERSION"
    wget https://github.com/prometheus/node_exporter/releases/download/v$NODE_EXPORTER_VERSION/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz || error_exit "Download failed."

    # Extract and install
    log_info "Extracting Node Exporter..."
    tar -xvf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz -C $INSTALL_DIR || error_exit "Failed to extract Node Exporter."
    cd $INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64 || error_exit "Failed to change directory."
    sudo ln -s "$INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" "$SYMLINK_PATH" || error_exit "Failed to create symlink at $SYMLINK_PATH."
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
    cd $INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64 || error_exit "Failed to change directory."
    sudo ln -s "$INSTALL_DIR/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" "$SYMLINK_PATH" || error_exit "Failed to create symlink at $SYMLINK_PATH."
}

function system_information {
    echo -e "\033[1;36m-------------------------------System Information----------------------------\033[0m"

    # Enhanced OS detection
    if [[ -f /etc/redhat-release ]]; then
        OS_VERSION=$(cat /etc/redhat-release)
        # Extract major version for CentOS/RHEL
        MAJOR_VERSION=$(echo "$OS_VERSION" | grep -oE '[0-9]+\.' | cut -d. -f1)
        echo -e "\033[1;36m* Operating System: $OS_VERSION\033[0m"
        echo -e "\033[1;36m* Major Version: $MAJOR_VERSION\033[0m"
    elif [[ -f /etc/os-release ]]; then
        OS_NAME=$(grep '^NAME=' /etc/os-release | cut -d= -f2 | tr -d '"')
        OS_VERSION=$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
        echo -e "\033[1;36m* Operating System: $OS_NAME $OS_VERSION\033[0m"
    else
        OS_NAME=$(uname -s)
        OS_VERSION=$(uname -r)
        echo -e "\033[1;36m* Operating System: $OS_NAME $OS_VERSION\033[0m"
    fi

    # Detect and display init system
    detect_init_system
    echo -e "\033[1;36m* Init System: $INIT_SYSTEM\033[0m"
    echo ""

    # Check if Node Exporter is running
    if ps -ef | grep 'node_exporter' | grep -v grep | grep -v installer | grep -v vi > /dev/null; then
        echo -e "\033[1;31m* Node Exporter is running...\033[0m"
        ps -ef | grep 'node_exporter' | grep -v grep | grep -v installer | grep -v vi
        echo ""
    else
        echo -e "\033[1;36m* Node Exporter is not running\033[0m"
        echo ""
    fi

    # Check port availability
    if ss -tulnp | grep ":$PORT" > /dev/null; then
        echo -e "\033[1;31m* Port 9100 is listening...\033[0m"
        ss -tulnp | grep ":$PORT"
        PORT=38001
        while true; do
            if ss -tulnp | grep ":$PORT" > /dev/null; then
                echo -e "\033[1;31m* Port $PORT is listening...\033[0m"
                ss -tulnp | grep ":$PORT"
                ((PORT+=1))
            else
                break
            fi
        done
        log_info "The port has been changed to \"$PORT\"."
    else
        echo -e "\033[1;36m* Port 9100 is not using...\033[0m"
    fi
    echo -e "\033[1;36m-----------------------------------------------------------------------------\033[0m"
}

# Configure Node Exporter as a sysvinit service
function configure_sysvinit_service {
    log_info "Configuring Node Exporter as a sysvinit service..."

    cat > /etc/init.d/node_exporter <<EOF
#!/bin/bash
#
# node_exporter    Node Exporter
#
# chkconfig: 2345 80 20
# description: Node Exporter for Prometheus
# processname: node_exporter
# pidfile: /var/run/node_exporter.pid

### BEGIN INIT INFO
# Provides:          node_exporter
# Required-Start:    \$local_fs \$network \$named \$time
# Required-Stop:     \$local_fs \$network \$named \$time
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Node Exporter
# Description:       Node Exporter for Prometheus monitoring
### END INIT INFO

# Source function library
. /etc/init.d/functions

DAEMON=$SYMLINK_PATH
DAEMON_ARGS="--web.listen-address=:$PORT"
NAME=node_exporter
PIDFILE=/var/run/\${NAME}.pid
LOGFILE=/var/log/\${NAME}.log
USER=root

start() {
    echo -n \$"Starting \$NAME: "
    daemon --pidfile=\$PIDFILE "\$DAEMON \$DAEMON_ARGS >> \$LOGFILE 2>&1 & echo \\\$! > \$PIDFILE"
    RETVAL=\$?
    echo
    return \$RETVAL
}

stop() {
    echo -n \$"Stopping \$NAME: "
    killproc -p \$PIDFILE \$NAME
    RETVAL=\$?
    echo
    [ \$RETVAL = 0 ] && rm -f \$PIDFILE
    return \$RETVAL
}

restart() {
    stop
    start
}

case "\$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status -p \$PIDFILE \$NAME
        ;;
    restart|reload)
        restart
        ;;
    *)
        echo \$"Usage: \$0 {start|stop|status|restart}"
        exit 1
esac

exit \$?
EOF

    chmod +x /etc/init.d/node_exporter
    chkconfig --add node_exporter
    chkconfig node_exporter on
    service node_exporter start

    log_info "SysVInit service configuration completed"
}

# Modified configure_service function
function configure_service {
    if [[ "$INIT_SYSTEM" == "systemd" ]]; then
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
    else
        configure_sysvinit_service
    fi

    log_info "Node Exporter installation and configuration completed."
}

# 시스템 정보 표시
system_information

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
