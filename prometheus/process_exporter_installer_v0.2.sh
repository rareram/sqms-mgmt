#!/bin/bash

# Default values for installation
DEFAULT_BINARY_PATH="$(pwd)/process-exporter-0.8.4.linux-amd64.tar.gz"
DEFAULT_INSTALL_DIR="/opt/monitoring/process_exporter"
DEFAULT_PROCESS_EXPORTER_VERSION="0.8.4"
SYMLINK_PATH="/usr/local/bin/process_exporter"
PORT=9256
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
    echo -e "\033[1;33m[ERROR] $1\033[0m"
}

if [[ $(id -u) -ne 0 ]]; then
    error_exit "This script must be run as root"
fi

# Enhanced system information detection
function detect_init_system {
    if command -v systemctl >/dev/null 2>&1 && pidof systemd >/dev/null 2>&1; then
        INIT_SYSTEM="systemd"
    elif [[ -f /etc/init.d/functions ]] || [[ -f /etc/rc.d/init.d/functions ]]; then
        INIT_SYSTEM="sysvinit"
    elif [[ -f /etc/init/rc.conf ]]; then
        INIT_SYSTEM="upstart"
    else
        log_error "Unable to detect init system. Defaulting to systemd..."
        INIT_SYSTEM="systemd"
    fi
    
    log_info "Detected init system: $INIT_SYSTEM"
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

    # Check if Process Exporter is running
    if ps -ef | grep 'process_exporter' | grep -v grep | grep -v installer | grep -v vi > /dev/null; then
        echo -e "\033[1;31m* Process Exporter is running...\033[0m"
        ps -ef | grep 'process_exporter' | grep -v grep | grep -v installer | grep -v vi
        echo ""
    else
        echo -e "\033[1;36m* Process Exporter is not running\033[0m"
        echo ""
    fi

    # Check port availability using netstat or ss
    if command -v ss >/dev/null 2>&1; then
        PORT_CHECK="ss -tulnp | grep \"LISTEN.*:$PORT\""
    else
        PORT_CHECK="netstat -tulnp | grep \"LISTEN.*:$PORT\""
    fi

    if eval "$PORT_CHECK" > /dev/null; then
        echo -e "\033[1;31m* Port $PORT is listening...\033[0m"
        eval "$PORT_CHECK"
        PORT=38001
        while true; do
            if command -v ss >/dev/null 2>&1; then
                CHECK_CMD="ss -tulnp | grep \"LISTEN.*:$PORT\""
            else
                CHECK_CMD="netstat -tulnp | grep \"LISTEN.*:$PORT\""
            fi
            if eval "$CHECK_CMD" > /dev/null; then
                echo -e "\033[1;31m* Port $PORT is listening...\033[0m"
                eval "$CHECK_CMD"
                ((PORT+=1))
            else
                break
            fi
        done
        log_info "The port has been changed to \"$PORT\"."
    else
        echo -e "\033[1;36m* Port $PORT is not using...\033[0m"
    fi
    echo -e "\033[1;36m-----------------------------------------------------------------------------\033[0m"
}

function check_install_directory {
    if [[ ! -d "$INSTALL_DIR" ]] ; then
        log_info "Installation directory does not exist. Creating $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR" || error_exit "Failed to create directory $INSTALL_DIR."
    fi
}

function check_selinux {
    if command -v getenforce >/dev/null 2>&1; then
        if [[ $(getenforce) == "Enforcing" ]]; then
            # error_exit "SELinux is enabled. You need to disable..(e.g. setenforce 0)"
            echo -e "\033[1;35m[WARNING] SELinux is enabled. You might need to configure SELinux policy.\033[0m"
        fi
    fi
}

function check_installation {
    if [[ -f "$SYMLINK_PATH" ]]; then
        binary=$(command -v process_exporter)
        if process_exporter --version >/dev/null 2>&1; then
            version=$(process_exporter --version 2>&1 | head -1)
        else
            version="version unknown"
        fi
        error_exit "Process Exporter is already installed. ($version)"
    fi
}

function create_config {
    local CONFIG_PATH="$INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64/config.yml"
    sudo tee "$CONFIG_PATH" > /dev/null <<EOF
process_names:
  - name: "{{.Comm}}({{.PID}}) [USER: {{.Username}}]"
    cmdline:
    - '.+'
EOF
    log_info "Created config file at $CONFIG_PATH"
}

function online_install {
    log_info "Starting online installation of Process Exporter..."

    if [[ -f process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz ]]; then
        log_info "File exists \"process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz\""
    else
        log_info "Downloading Process Exporter version: $PROCESS_EXPORTER_VERSION"
        wget https://github.com/ncabatoff/process-exporter/releases/download/v$PROCESS_EXPORTER_VERSION/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz || error_exit "Download failed."
    fi

    # Extract and install
    log_info "Extracting Process Exporter..."
    tar -xvf process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz -C $INSTALL_DIR || error_exit "Failed to extract Process Exporter."
    cd $INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64 || error_exit "Failed to change directory."
    sudo ln -s "$INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64/process-exporter" "$SYMLINK_PATH" || error_exit "Failed to create symlink at $SYMLINK_PATH."

    # Create config file
    create_config
}

function offline_install {
    [[ -z "$BINARY_PATH" ]] && error_exit "Binary path must be provided for offline installation."

    log_info "Starting offline installation of Process Exporter..."
    [[ ! -f "$BINARY_PATH" ]] && error_exit "File not found at $BINARY_PATH."
    PROCESS_EXPORTER_VERSION=$(echo "$BINARY_PATH" | sed -E 's/.*process-exporter-([0-9\.]+)\..*/\1/')
    [[ "$BINARY_PATH" == $PROCESS_EXPORTER_VERSION ]] && error_exit "Failed to extract process-exporter version from filename: $BINARY_PATH"

    log_info "Extracting Process Exporter from provided path..."
    tar -xvf "$BINARY_PATH" -C $INSTALL_DIR || error_exit "Failed to extract Process Exporter from $BINARY_PATH."
    cd $INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64 || error_exit "Failed to change directory."
    sudo ln -s "$INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64/process-exporter" "$SYMLINK_PATH" || error_exit "Failed to create symlink at $SYMLINK_PATH."

    # Create config file
    create_config
}

function configure_sysvinit_service {
    log_info "Configuring Process Exporter as a sysvinit service..."

    cat > /etc/init.d/process_exporter <<EOF
#!/bin/bash
#
# process_exporter    Process Exporter
#
# chkconfig: 2345 80 20
# description: Process Exporter for Prometheus
# processname: process_exporter
# pidfile: /var/run/process_exporter.pid

### BEGIN INIT INFO
# Provides:          process_exporter
# Required-Start:    \$local_fs \$network \$named \$time
# Required-Stop:     \$local_fs \$network \$named \$time
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Process Exporter
# Description:       Process Exporter for Prometheus monitoring
### END INIT INFO

# Source function library
. /etc/init.d/functions

DAEMON=$SYMLINK_PATH
CONFIG_PATH="$INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64/config.yml"
DAEMON_ARGS="--config.path=\$CONFIG_PATH --web.listen-address=:$PORT"
NAME=process_exporter
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

    chmod +x /etc/init.d/process_exporter
    chkconfig --add process_exporter
    chkconfig process_exporter on
    service process_exporter start || error_exit "Failed to start Process Exporter service"

    log_info "SysVInit service configuration completed"
}

function configure_service {
    if [[ "$INIT_SYSTEM" == "systemd" ]]; then
        log_info "Configuring Process Exporter as a systemd service..."

        sudo tee /etc/systemd/system/process_exporter.service > /dev/null <<EOF
[Unit]
Description=Process Exporter
Wants=network-online.target
After=network-online.target

[Service]
ExecStart=$SYMLINK_PATH --config.path=$INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64/config.yml --web.listen-address=:$PORT

[Install]
WantedBy=multi-user.target
EOF

        log_info "Enabling and starting Process Exporter service..."
        sudo systemctl daemon-reload || error_exit "Failed to reload systemd."
        sudo systemctl enable process_exporter || error_exit "Failed to enable Process Exporter service."
        sudo systemctl start process_exporter || error_exit "Failed to start Process Exporter service."
    else
        configure_sysvinit_service
    fi

    log_info "Process Exporter installation and configuration completed."
}

function uninstall {
    log_info "Uninstalling Process Exporter..."

    # 실행 중인 프로세스 중지 - 모든 방식 시도
    if command -v systemctl >/dev/null 2>&1; then
        systemctl stop process_exporter 2>/dev/null || log_error "Failed to stop Process Exporter via systemctl"
        systemctl disable process_exporter 2>/dev/null || log_error "Failed to disable Process Exporter service"
        rm -f /etc/systemd/system/process_exporter.service 2>/dev/null || log_error "Failed to remove systemd service file"
        systemctl daemon-reload 2>/dev/null
    fi
    
    service process_exporter stop 2>/dev/null || log_error "Failed to stop Process Exporter via service command"
    chkconfig process_exporter off 2>/dev/null || log_error "Failed to disable Process Exporter via chkconfig"
    rm -f /etc/init.d/process_exporter 2>/dev/null || log_error "Failed to remove init.d script"

    # 프로세스가 여전히 실행 중인지 확인
    if pgrep -f "process_exporter" > /dev/null; then
        log_error "Process Exporter process is still running. Attempting to kill..."
        pkill -f "process_exporter" || log_error "Failed to kill Process Exporter process"
    fi

    # 파일 정리
    if [[ -f "$SYMLINK_PATH" ]]; then
        rm -f "$SYMLINK_PATH" || error_exit "Failed to remove symlink $SYMLINK_PATH"
    fi

    DELETE_DIR="$INSTALL_DIR/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64"
    if [[ -d "$DELETE_DIR" ]]; then
        rm -rf "$DELETE_DIR" || error_exit "Failed to remove Process Exporter directory $DELETE_DIR"
    fi

    log_info "Process Exporter has been uninstalled successfully."
    exit 0
}

# Display system information
system_information

# Handle installation mode selection
while true; do
    case "$INSTALL_MODE_INPUT" in
        1)
            INSTALL_MODE="online"
            read -p "Enter the Process Exporter version to install (default: $DEFAULT_PROCESS_EXPORTER_VERSION): " PROCESS_EXPORTER_VERSION
            PROCESS_EXPORTER_VERSION=${PROCESS_EXPORTER_VERSION:-$DEFAULT_PROCESS_EXPORTER_VERSION}
            break
            ;;
        2)
            INSTALL_MODE="offline"
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
            ;;
    esac
done

if [[ "$INSTALL_MODE" == "uninstall" ]]; then
    PROCESS_EXPORTER_VERSION=${BINARY_PATH:-$DEFAULT_PROCESS_EXPORTER_VERSION}
    read -p "Enter the uninstallation directory (default: $DEFAULT_INSTALL_DIR): " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}

    read -p "Proceed with the uninstallation? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
        echo "Uninstallation aborted."
        exit 0
    fi
else
    read -p "Enter the installation directory (default: $DEFAULT_INSTALL_DIR): " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}

    echo "-----------------------------------------------------------------------------------------"
    echo "Installation mode: $INSTALL_MODE"
    if [[ "$INSTALL_MODE" == "offline" ]]; then
        echo "Installation file path: $BINARY_PATH"
    fi
    echo "Installation directory: $INSTALL_DIR"

    read -p "Proceed with the installation? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
        echo "Installation aborted."
        exit 0
    fi
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

# Configure Process Exporter service if not uninstalling
if [[ "$INSTALL_MODE" != "uninstall" ]]; then
    configure_service
    log_info "Installation finished successfully."
fi
