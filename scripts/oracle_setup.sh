#!/bin/bash

# Project Andrew - Oracle Cloud Provisioning Script
# Requires OCI CLI to be installed and configured (`oci setup config`)

echo "Starting Oracle Cloud Provisioning for Project Andrew..."

# Replace these with your actual OCI compartment and subnet OCIDs
COMPARTMENT_ID="ocid1.compartment.oc1..your_compartment_id"
SUBNET_ID="ocid1.subnet.oc1..your_subnet_id"
IMAGE_ID="ocid1.image.oc1..aarch64_ubuntu_2204" # Ubuntu 22.04 ARM Image

echo "Provisioning VM.Standard.A1.Flex (4 OCPU, 24GB RAM)..."

INSTANCE_JSON=$(oci compute instance launch \
    --availability-domain "AD-1" \
    --compartment-id "$COMPARTMENT_ID" \
    --shape "VM.Standard.A1.Flex" \
    --shape-config '{"ocpus": 4, "memoryInGBs": 24}' \
    --subnet-id "$SUBNET_ID" \
    --image-id "$IMAGE_ID" \
    --assign-public-ip true \
    --display-name "Andrew-Core" \
    --ssh-authorized-keys-file ~/.ssh/id_rsa.pub \
    --wait-for-state RUNNING)

PUBLIC_IP=$(echo $INSTANCE_JSON | jq -r '.data."public-ip"')
echo "Instance Provisioned Successfully! Public IP: $PUBLIC_IP"

echo "Waiting for SSH to become available..."
sleep 30

echo "Installing Docker and Ollama on the remote instance..."
ssh -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << 'EOF'
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    echo "Installing Ollama for ARM CPU inference..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    echo "Setup Complete!"
EOF

echo "--- NEXT STEPS ---"
echo "1. SCP your Kaggle-trained andrew_model-unsloth.Q8_0.gguf to the server:"
echo "   scp andrew_model-unsloth.Q8_0.gguf ubuntu@$PUBLIC_IP:~/"
echo "2. Create a Modelfile on the server and run: ollama create andrew -f Modelfile"
echo "3. Run your FastAPI backend on the server."
