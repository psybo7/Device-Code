### Structure
The tool is composed of:
- an HTML + JS frontend hosted by Caddy;
- a Python Flask backend.

### Logic

When the victim visits the malicious webpage, a JavaScript code embedded in the HTML contacts the backend to obtain a USER CODE to be used in the context of the Device Code Flow.
Upon receiving the request, the backend sends a message to Microsoft’s /devicecode API to obtain a USER CODE and a DEVICE CODE. Once the USER CODE is received, it is sent to the frontend and displayed in the victim's browser.
At this point, the victim is prompted to connect to the /devicelogin API, where they must first enter the alphanumeric code and then their credentials.
Meanwhile, the backend tracks the victim's visit and continues polling Microsoft’s /token API for up to 15 minutes (the validity period of the device code).
If, within the allowed time frame, the victim enters their credentials, the device code is validated, allowing the attacker to obtain an Access Token and a Refresh Token.
By default, the software requests OAUTH 2 tokens for the resource https://graph.windows.net.

### Steps
Run the software with:
`docker-compose up -d`

Access your landing page hostname

To monitor operations:
`docker-compose logs -f flask`

### Victim Flow
1. Victim visits phishing page
2. JS requests /proxy/devicecode → Flask generates USER_CODE
3. Victim enters code at https://microsoft.com/devicelogin
4. Backend polls /token → Captures Access/Refresh tokens in ./flask_data/
5. Tokens logged and saved to SQLite/file when victim authenticates (15min window).

