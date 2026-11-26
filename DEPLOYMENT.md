# Deployment

These steps put the app on a Linux virtual machine in the cloud so that it opens at
`http://<server-ip>`. The example uses Ubuntu 24.04. Azure for Students, Oracle Cloud
Free Tier and AWS Free Tier all work the same way, only the menu names differ.

## 1. Create the server

1. Sign up to the provider with the student offer or free tier.
2. Create a virtual machine:
   - Image: Ubuntu 24.04 LTS
   - Size: the smallest free one (1 vCPU, 1 GB RAM is enough)
   - Authentication: SSH key (download the private key, e.g. `autorepair.pem`)
3. In the network settings of the VM, allow inbound traffic on **port 22 (SSH)** and **port 80 (HTTP)**.
   - Azure: Networking → Add inbound port rule
   - Oracle: VCN → Security List → Add Ingress Rule
   - AWS: Security Group → Edit inbound rules
4. Note the **public IP address** of the VM.

## 2. Connect and install Docker

```bash
chmod 400 autorepair.pem
ssh -i autorepair.pem azureuser@<server-ip>      # user is "ubuntu" on AWS and Oracle

sudo apt update
sudo apt install -y git docker.io docker-compose-v2
sudo usermod -aG docker $USER
exit                                              # log out and in again so the group change applies
```

If `docker-compose-v2` is not found, install Docker with the official script instead:
`curl -fsSL https://get.docker.com | sudo sh`

## 3. Get the project and start it

```bash
ssh -i autorepair.pem azureuser@<server-ip>
git clone https://github.com/<user>/autorepair-database-system-group-X.git
cd autorepair-database-system-group-X

cp .env.example .env
nano .env        # set APP_PORT=80, a new DB_PASSWORD and a long random SECRET_KEY

docker compose up -d --build
docker compose ps        # both services should be "running" / "healthy"
```

## 4. Open the firewall on the VM

Oracle Cloud Ubuntu images block port 80 inside the VM as well:

```bash
sudo iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

If `ufw` is active on your image: `sudo ufw allow 80/tcp`.

## 5. Check

Open `http://<server-ip>` in a browser and log in with a test account from `README.md`.

## Updating after a new commit

```bash
cd autorepair-database-system-group-X
git pull
docker compose up -d --build
```

## Bonus: domain name

1. Buy a cheap domain (under 50 TL) from a registrar.
2. In the registrar's DNS settings add an **A record**: host `@`, value `<server-ip>`.
   Optionally add another A record with host `www`.
3. After the DNS change spreads (a few minutes to a few hours), the app opens at `http://<your-domain>`.
