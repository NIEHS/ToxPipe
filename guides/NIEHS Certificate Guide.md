# ToxPipe: Installing and Using NIEHS SSL Certificates in Python
When attempting to call ToxPipe's AI models in Python, you may run into errors like:

`httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain`

This is a brief guide to fixing SSL errors when attempting to access ToxPipe models and other resources.

## Step 1: Get Certificates
You will first need to download the SSL certificates for ToxPipe. You can do this in Chrome by visiting https://toxpipe.niehs.nih.gov/ and:
1. Click the icon to the left of the URL and click the "Connection is secure" area in the menu that shows up. ![](step1.png)
2. Click the icon to the right of the "Certificate is valid" area to view the certificates in a new menu. ![](step2.png)
3. In the new menu, click the **Details** tab. You should see 3 levels of certificate: NIH-DPKI-ROOT-1A, NIH-DPKI-CA-1A, and toxpipe.niehs.nih.gov. Click on each level so it is highlighted blue, and click the "Export..." button in the bottom right to download the certificate to your computer. ![](step3.png)

You may also receive the certificates by emailing parker.combs@nih.gov.

## Step 2: Install Certificates
We still need to install the certificates, so navigate to the location where you downloaded them to on your machine. The next steps will be different depending on your OS:

### Windows 11
1. Right click on each certificate, and click on the **Install Certificate** option in the menu that pops up. ![](step4.png)
2. The Certificate Import Wizard should open. Follow the instructions provided to install the certificate. Make sure you do this for all 3 certificates you downloaded earlier. ![](step5.png)

### MacOS
See https://support.apple.com/guide/keychain-access/add-certificates-to-a-keychain-kyca2431/mac.

### RHEL / Rocky Linux (need sudo access)
1. Move or copy the certificate files to `/etc/pki/ca-trust/source/anchors/`.
2. Run the command `sudo update-ca-trust extract`.

## Step 3: Point Python to the New Certificates
Finally, we need to tell our Python script to use the updated certificate store. The easiest way to do this is with the `truststore` package, which may be downloaded with the command `pip install truststore`.

After installing `truststore`, add the following lines to your Python script somewhere before your AI model calls:
```
import truststore
truststore.inject_into_ssl()
```
