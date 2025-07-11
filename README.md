# PyDentity Wallet

## Overview
PyDentity Wallet is a Python-based Progressive Web Application (PWA) designed to provide mobile wallet functionality for ACA-Py (Aries Cloud Agent Python). It enables seamless access to mobile wallet features and browser APIs, offering a frontend for managing multi-tenant ACA-Py instances.

## Features
- **Multi-Tenant ACA-Py Support**: Connects to ACA-Py instances and allows users to manage subwallets.
- **Mobile Device Binding**: Securely stores wallet data in an ecrypted remote session bound to a mobile device.
- **Cross-Platform Compatibility**: Works on iOS and Android via browser-based access.
- **Open Standards Compliance**: Utilizes W3C, IETF, DIF, and other open standards whenever possible.

## Project Status
PyDentity Wallet is currently in the **Labs** stage under the OpenWallet Foundation. The project is actively developed as an open-source initiative to enhance the usability of decentralized identity solutions.

## Usage
### Development
To get started quickly, you can leverage the development agent available and an ngrok tunnel for the server.

### Pre-requisites
- Free NGROK account and auth token
- Docker installed

Clone this repository, then create your .env file:
```bash
git clone git@github.com:openwallet-foundation-labs/PyDentity-Wallet.git
cd PyDentity-Wallet
cp .env.example .env

```

Fill the `.env` file with your NGROK token and the following values:
```bash
AGENT_ADMIN_API_KEY=pydentity
AGENT_ADMIN_ENDPOINT=https://admin.dev.pydentity.net
NGROK_AUTHTOKEN=enter-ngrok-token
```

Build the image and run the server:
```
docker build --tag pydentity-wallet --file docker/Dockerfile .
docker run --env-file .env pydentity-wallet

```

- **Connecting to ACA-Py**: Enter your ACA-Py instance details to authenticate and access wallet functionality.
- **Managing Credentials**: Store, view, and share verifiable credentials securely.
- **Interacting with DIDs**: Establish and manage secure DID-based connections.

### Creating an instance
- Upon your first visit to the app domain, you will be prompted to create a webauthn login credential. Fingerprint binding is our recommended method.
- When you visit the domain successively, you will be promtped to login with your webauthn login credential.
- If you clear the page data in your browser, you will permanently loose access to your instance, beware.
    - Email recovery might be a feature made available in the future.

## Contribution
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch.
3. Commit changes and push to your fork.
4. Submit a pull request.

## License
PyDentity Wallet is open-source and licensed under the Apache 2.0 License.

## Alignment with OpenWallet Foundation
This project aligns with the **OpenWallet Foundation (OWF)** mission by implementing open wallet standards and enhancing an existing OWF impact project. It fosters interoperability and accessibility in the decentralized identity ecosystem.

## Contact
For inquiries and contributions, reach out via the repository’s issue tracker or join our discussions on the OWF community channels.

