#!/bin/bash

# Script to fix Redis memory overcommit issue
# This script should be run on the host system before starting Docker containers

echo "Checking current memory overcommit settings..."

# Check current overcommit memory setting
CURRENT_SETTING=$(cat /proc/sys/vm/overcommit_memory 2>/dev/null || echo "unknown")
echo "Current vm.overcommit_memory setting: $CURRENT_SETTING"

# Check if the setting is already correct
if [ "$CURRENT_SETTING" = "1" ]; then
    echo "Memory overcommit is already correctly set to 1."
    exit 0
fi

# Fix the memory overcommit setting
echo "Setting vm.overcommit_memory to 1..."
echo 1 > /proc/sys/vm/overcommit_memory 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Failed to set vm.overcommit_memory. Trying with sudo..."
    sudo echo 1 > /proc/sys/vm/overcommit_memory 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Could not set vm.overcommit_memory. Please run this script with sudo privileges."
        echo "Alternatively, you can manually run: sudo sysctl vm.overcommit_memory=1"
        exit 1
    fi
fi

# Make the change permanent by adding to /etc/sysctl.conf
echo "Making the change permanent..."
SYSCTL_LINE="vm.overcommit_memory = 1"

# Check if the line already exists in /etc/sysctl.conf
if grep -q "^vm.overcommit_memory" /etc/sysctl.conf 2>/dev/null; then
    echo "Updating existing vm.overcommit_memory setting in /etc/sysctl.conf..."
    sudo sed -i 's/^vm.overcommit_memory.*/vm.overcommit_memory = 1/' /etc/sysctl.conf
else
    echo "Adding vm.overcommit_memory setting to /etc/sysctl.conf..."
    echo "$SYSCTL_LINE" | sudo tee -a /etc/sysctl.conf > /dev/null
fi

# Verify the change
echo "Verifying the change..."
NEW_SETTING=$(cat /proc/sys/vm/overcommit_memory 2>/dev/null || echo "unknown")
echo "New vm.overcommit_memory setting: $NEW_SETTING"

if [ "$NEW_SETTING" = "1" ]; then
    echo "SUCCESS: Memory overcommit has been correctly set to 1."
    echo "This change will prevent Redis from failing under low memory conditions."
else
    echo "WARNING: Failed to set vm.overcommit_memory to 1."
    echo "Please manually run: sudo sysctl vm.overcommit_memory=1"
    exit 1
fi

echo "Memory overcommit fix completed successfully."