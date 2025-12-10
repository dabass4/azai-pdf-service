# AZAI Dependency Status Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S %Z')

---

## 📊 Summary


- **Python Packages:** 166 installed
- **JavaScript Packages:** 74 dependencies
- **System Dependencies:** poppler-utils, MongoDB

---

## 🔒 Security Status


### Python Security Audit

```
\033[1;33m[1/2] Checking Python dependencies for vulnerabilities...\033[0m
--------------------------------------
\033[0;31m⚠️  Security vulnerabilities detected in Python packages!\033[0m
Found 7 known vulnerabilities in 5 packages
Name            Version ID             Fix Versions Description
--------------- ------- -------------- ------------ -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ecdsa           0.19.1  CVE-2024-23342              python-ecdsa has been found to be subject to a Minerva timing attack on the P-256 curve. Using the `ecdsa.SigningKey.sign_digest()` API function and timing signatures an attacker can leak the internal nonce which may allow for private key discovery. Both ECDSA signatures, key generation, and ECDH operations are affected. ECDSA signature verification is unaffected. The python-ecdsa project considers side channel attacks out of scope for the project and there is no planned fix.
pymongo         4.5.0   CVE-2024-5629  4.6.3        Versions of the package pymongo before 4.6.3 are vulnerable to Out-of-bounds Read in the bson module. Using the crafted payload the attacker could force the parser to deserialize unmanaged memory. The parser tries to interpret bytes next to buffer and throws an exception with string. If the following bytes are not printable UTF-8 the parser throws an exception with a single byte.
python-socketio 5.11.0  CVE-2025-61765 5.14.0       ### Summary A remote code execution vulnerability in python-socketio versions prior to 5.14.0 allows attackers to execute arbitrary Python code through malicious pickle deserialization in multi-server deployments on which the attacker previously gained access to the message queue that the servers use for internal communications.  ### Details When Socket.IO servers are configured to use a message queue backend such as Redis for inter-server communication, messages sent between the servers are encoded using the `pickle` Python module. When a server receives one of these messages through the message queue, it assumes it is trusted and immediately deserializes it.  The vulnerability stems from deserialization of messages using Python's `pickle.loads()` function. Having previously obtained access to the message queue, the attacker can send a python-socketio server a crafted pickle payload that executes arbitrary code during deserialization via Python's `__reduce__` method.  ### Impact This vulnerability only affects deployments with a compromised message queue. The attack can lead to the attacker executing random code in the context of, and with the privileges of a Socket.IO server process.   Single-server systems that do not use a message queue, and multi-server systems with a secure message queue are not vulnerable.  ### Remediation In addition to making sure standard security practices are followed in the deployment of the message queue, users of the python-socketio package can upgrade to version 5.14.0 or newer, which remove the `pickle` module and use the much safer JSON encoding for inter-server messaging.
starlette       0.37.2  CVE-2024-47874 0.40.0       ### Summary Starlette treats `multipart/form-data` parts without a `filename` as text form fields and buffers those in byte strings with no size limit. This allows an attacker to upload arbitrary large form fields and cause Starlette to both slow down significantly due to excessive memory allocations and copy operations, and also consume more and more memory until the server starts swapping and grinds to a halt, or the OS terminates the server process with an OOM error. Uploading multiple such requests in parallel may be enough to render a service practically unusable, even if reasonable request size limits are enforced by a reverse proxy in front of Starlette.  ### PoC  ```python from starlette.applications import Starlette from starlette.routing import Route  async def poc(request):     async with request.form():         pass  app = Starlette(routes=[     Route('/', poc, methods=["POST"]), ]) ```  ```sh curl http://localhost:8000 -F 'big=</dev/urandom' ```  ### Impact This Denial of service (DoS) vulnerability affects all applications built with Starlette (or FastAPI) accepting form requests.
starlette       0.37.2  CVE-2025-54121 0.47.2       ### Summary When parsing a multi-part form with large files (greater than the [default max spool size](https://github.com/encode/starlette/blob/fa5355442753f794965ae1af0f87f9fec1b9a3de/starlette/formparsers.py#L126)) `starlette` will block the main thread to roll the file over to disk. This blocks the event thread which means we can't accept new connections.  ### Details Please see this discussion for details: https://github.com/encode/starlette/discussions/2927#discussioncomment-13721403. In summary the following UploadFile code (copied from [here](https://github.com/encode/starlette/blob/fa5355442753f794965ae1af0f87f9fec1b9a3de/starlette/datastructures.py#L436C5-L447C14)) has a minor bug. Instead of just checking for `self._in_memory` we should also check if the additional bytes will cause a rollover.  ```python      @property     def _in_memory(self) -> bool:         # check for SpooledTemporaryFile._rolled         rolled_to_disk = getattr(self.file, "_rolled", True)         return not rolled_to_disk      async def write(self, data: bytes) -> None:         if self.size is not None:             self.size += len(data)          if self._in_memory:             self.file.write(data)         else:             await run_in_threadpool(self.file.write, data) ```  I have already created a PR which fixes the problem: https://github.com/encode/starlette/pull/2962   ### PoC See the discussion [here](https://github.com/encode/starlette/discussions/2927#discussioncomment-13721403) for steps on how to reproduce.  ### Impact To be honest, very low and not many users will be impacted. Parsing large forms is already CPU intensive so the additional IO block doesn't slow down `starlette` that much on systems with modern HDDs/SSDs. If someone is running on tape they might see a greater impact.
```

### JavaScript Security Audit

```
No vulnerabilities found
```

---

## 📦 Outdated Packages


### Python Packages

```
\033[0;34m[1/2] Checking Python packages...\033[0m
--------------------------------------
Analyzing 154 Python packages...
\033[1;33m📦 46 Python packages have updates available\033[0m

Top 10 outdated packages:
Package                      Version    Latest     Type
---------------------------- ---------- ---------- -----
aiohttp                      3.13.1     3.13.2     wheel
anyio                        4.11.0     4.12.0     wheel
bcrypt                       4.1.3      5.0.0      wheel
black                        25.9.0     25.12.0    wheel
boto3                        1.40.59    1.42.6     wheel
botocore                     1.40.59    1.42.6     wheel
CacheControl                 0.14.3     0.14.4     wheel
cachetools                   6.2.1      6.2.2      wheel
certifi                      2025.10.5  2025.11.12 wheel
click                        8.3.0      8.3.1      wheel
fastapi                      0.110.1    0.124.0    wheel
fsspec                       2025.9.0   2025.12.0  wheel
google-ai-generativelanguage 0.6.15     0.9.0      wheel

\033[0;34m[2/2] Checking JavaScript packages...\033[0m
--------------------------------------
```

### JavaScript Packages

```
\033[0;34m[2/2] Checking JavaScript packages...\033[0m
--------------------------------------
Analyzing JavaScript packages...
\033[1;33m📦 JavaScript packages have updates available\033[0m

yarn outdated v1.22.22
info Color legend : 
 "<red>"    : Major Update backward-incompatible updates 
 "<yellow>" : Minor Update backward-compatible features 
 "<green>"  : Patch Update backward-compatible bug fixes
Package                      Current Wanted  Latest  Package Type    URL                                                
@eslint/js                   9.23.0  9.23.0  9.39.1  devDependencies https://eslint.org                                 
@radix-ui/react-aspect-ratio 1.1.7   1.1.8   1.1.8   dependencies    https://radix-ui.com/primitives                    
@radix-ui/react-avatar       1.1.10  1.1.11  1.1.11  dependencies    https://radix-ui.com/primitives                    
@radix-ui/react-label        2.1.7   2.1.8   2.1.8   dependencies    https://radix-ui.com/primitives                    
@radix-ui/react-progress     1.1.7   1.1.8   1.1.8   dependencies    https://radix-ui.com/primitives                    
@radix-ui/react-separator    1.1.7   1.1.8   1.1.8   dependencies    https://radix-ui.com/primitives                    
@radix-ui/react-slot         1.2.3   1.2.4   1.2.4   dependencies    https://radix-ui.com/primitives                    
autoprefixer                 10.4.21 10.4.22 10.4.22 devDependencies https://github.com/postcss/autoprefixer#readme     
axios                        1.13.1  1.13.2  1.13.2  dependencies    https://axios-http.com                             
cra-template                 1.2.0   1.2.0   1.3.0   dependencies    https://github.com/facebook/create-react-app#readme
eslint                       9.23.0  9.23.0  9.39.1  devDependencies https://eslint.org                                 
eslint-plugin-import         2.31.0  2.31.0  2.32.0  devDependencies https://github.com/import-js/eslint-plugin-import  
eslint-plugin-react          7.37.4  7.37.4  7.37.5  devDependencies https://github.com/jsx-eslint/eslint-plugin-react  
```

---

## 🎯 Recommendations

### High Priority (Security)
- Review and apply security patches immediately
- Test thoroughly after security updates

### Medium Priority (Bug Fixes)
- Update patch versions (x.x.X) monthly
- Review changelogs before applying

### Low Priority (Features)
- Evaluate major version updates quarterly
- Test in staging environment first

---

## 📋 Update Strategy

### For Healthcare/Medicaid Application:

1. **Security First**: Apply security patches within 48 hours
2. **Stability Over Features**: Prefer stable over latest
3. **Testing Required**: Full test suite before production
4. **Version Pinning**: Maintain exact versions for predictability
5. **Staged Rollout**: Update dev → staging → production

### Next Review Date

**Recommended:** $(date -d '+1 month' '+%Y-%m-%d')

---

*Report generated by AZAI Dependency Management System*
