import urllib.request
import re
import os

BASE_URL = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/"
TARGET_DIR = "apps/sunat/services"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

def download_and_patch(filename, url):
    print(f"Downloading {url} -> {filename}")
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
    
    # Replace location="..." or schemaLocation="..."
    # Example: location="billService?ns1.wsdl"
    # We will rename ? to _ for local files
    
    def replacer(match):
        full_match = match.group(0)
        attr = match.group(1) # location or schemaLocation
        ref_url = match.group(2)
        
        # if it's a relative sunat url
        if ref_url.startswith("billService"):
            local_name = ref_url.replace("?", "_").replace("=", "_")
            
            # Download recursively
            abs_url = BASE_URL + ref_url
            download_and_patch(os.path.join(TARGET_DIR, local_name), abs_url)
            
            return f'{attr}="{local_name}"'
        return full_match

    patched_content = re.sub(r'(location|schemaLocation)="([^"]+)"', replacer, content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(patched_content)

download_and_patch(os.path.join(TARGET_DIR, "billService.wsdl"), BASE_URL + "billService?wsdl")
print("Done downloading WSDLs.")
