import os
import ssl
import certifi

# Use certifi's certificate bundle
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Disable SSL verification as fallback
os.environ['PYTHONHTTPSVERIFY'] = '0'
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context