#!/bin/bash

# Script to automatically update and upgrade an Ubuntu system.

# Set variables
LOG_FILE="/var/log/auto-update.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Function to log messages
log() {
  echo "$TIMESTAMP: $1" >> "$LOG_FILE"
}

# Function to check for root privileges
check_root() {
  if [[ $EUID -ne 0 ]]; then
    log "Error: This script must be run as root."
    exit 1
  fi
}

# Function to update package lists
update_packages() {
  log "Updating package lists..."
  apt-get update -y 2>&1 | tee -a "$LOG_FILE"
  if [[ $? -ne 0 ]]; then
    log "Error: Failed to update package lists."
    exit 1
  fi
  log "Package lists updated successfully."
}

# Function to upgrade packages
upgrade_packages() {
  log "Upgrading packages..."
  apt-get upgrade -y 2>&1 | tee -a "$LOG_FILE"
  if [[ $? -ne 0 ]]; then
    log "Error: Failed to upgrade packages."
    exit 1
  fi
  log "Packages upgraded successfully."
}

# Function to perform a full distribution upgrade
#dist_upgrade() {
#  log "Performing distribution upgrade..."
#  apt-get dist-upgrade -y 2>&1 | tee -a "$LOG_FILE"
#  if [[ $? -ne 0 ]]; then
#    log "Error: Failed to perform distribution upgrade."
#    exit 1
#  fi
#  log "Distribution upgrade completed successfully."
#}

# Function to remove unused packages
autoremove_packages() {
  log "Removing unused packages..."
  apt-get autoremove -y 2>&1 | tee -a "$LOG_FILE"
  if [[ $? -ne 0 ]]; then
    log "Error: Failed to remove unused packages."
    exit 1
  fi
  log "Unused packages removed successfully."
}

# Function to clean up the package cache
autoclean_packages() {
  log "Cleaning package cache..."
  apt-get autoclean -y 2>&1 | tee -a "$LOG_FILE"
  if [[ $? -ne 0 ]]; then
    log "Error: Failed to clean package cache."
    exit 1
  fi
  log "Package cache cleaned successfully."
}

# Main script execution
check_root
update_packages
upgrade_packages
#dist_upgrade
autoremove_packages
autoclean_packages

log "Automatic update and upgrade completed."

exit 0
