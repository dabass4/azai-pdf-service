"""OMES EDI SFTP Client for Batch File Submissions

Handles:
- Upload 837 claim files to SFTP
- Download 835 remittance advice
- Download 277 acknowledgments
- Download 999 functional acknowledgments
"""

import os
import logging
from typing import List, Optional
from datetime import datetime
import paramiko
from io import StringIO
import time

logger = logging.getLogger(__name__)


class OMESSFTPClient:
    """Client for OMES EDI SFTP batch file transfers"""
    
    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 private_key_path: Optional[str] = None,
                 tpid: Optional[str] = None):
        """
        Initialize OMES SFTP client
        
        Args:
            host: SFTP server hostname
            port: SFTP port (default 22)
            username: SFTP username
            password: SFTP password (if not using key auth)
            private_key_path: Path to SSH private key
            tpid: 7-digit Trading Partner ID
        """
        self.host = host or os.getenv("OMES_SFTP_HOST", "mft-dev.oh.healthinteractive.net")
        self.port = port or int(os.getenv("OMES_SFTP_PORT", "22"))
        self.username = username or os.getenv("OMES_SFTP_USERNAME", "")
        self.password = password or os.getenv("OMES_SFTP_PASSWORD", "")
        self.private_key_path = private_key_path or os.getenv("OMES_SFTP_KEY_PATH", "")
        self.tpid = tpid or os.getenv("OMES_TPID", "0000000")
        
        # SFTP directory structure
        self.env = os.getenv("OMES_ENV", "CERT")  # CERT or PRD
        self.inbound_folder = f"/{self.env}/EDI_IN/{self.tpid}_INBOUND"
        self.outbound_folder = f"/{self.env}/EDI_OUT/{self.tpid}_OUTBOUND"
        
        self._sftp_client = None
        self._ssh_client = None
    
    def _load_private_key(self) -> Optional[paramiko.RSAKey]:
        """Load SSH private key from file"""
        if not self.private_key_path or not os.path.exists(self.private_key_path):
            return None
        
        try:
            return paramiko.RSAKey.from_private_key_file(self.private_key_path)
        except Exception as e:
            logger.error(f"Failed to load private key: {str(e)}")
            return None
    
    def connect(self):
        """Establish SFTP connection"""
        if self._sftp_client is not None:
            return  # Already connected
        
        try:
            # Create SSH client
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with key or password authentication
            private_key = self._load_private_key()
            
            if private_key:
                logger.info(f"Connecting to {self.host}:{self.port} with key authentication")
                self._ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=30
                )
            else:
                logger.info(f"Connecting to {self.host}:{self.port} with password authentication")
                self._ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
            
            # Open SFTP session
            self._sftp_client = self._ssh_client.open_sftp()
            logger.info(f"SFTP connection established to {self.host}")
            
        except Exception as e:
            logger.error(f"SFTP connection failed: {str(e)}")
            raise Exception(f"Failed to connect to OMES SFTP: {str(e)}")
    
    def disconnect(self):
        """Close SFTP connection"""
        if self._sftp_client:
            self._sftp_client.close()
            self._sftp_client = None
        
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
        
        logger.info("SFTP connection closed")
    
    def upload_claim_file(self, file_content: str, filename: Optional[str] = None) -> str:
        """
        Upload 837 claim file to SFTP inbound folder
        
        Args:
            file_content: EDI file content (X12 format)
            filename: Optional custom filename
        
        Returns:
            Filename of uploaded file
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"837_{self.tpid}_{timestamp}.txt"
        
        try:
            self.connect()
            
            # Upload file to inbound folder
            remote_path = f"{self.inbound_folder}/{filename}"
            
            # Write content to remote file
            with self._sftp_client.file(remote_path, 'w') as remote_file:
                remote_file.write(file_content)
            
            logger.info(f"Uploaded claim file: {filename} ({len(file_content)} bytes)")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to upload claim file: {str(e)}")
            raise Exception(f"SFTP upload failed: {str(e)}")
        finally:
            self.disconnect()
    
    def list_response_files(self) -> List[str]:
        """
        List all files in outbound folder
        
        Returns:
            List of filenames
        """
        try:
            self.connect()
            
            # List files in outbound folder
            files = self._sftp_client.listdir(self.outbound_folder)
            
            logger.info(f"Found {len(files)} response files in {self.outbound_folder}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list response files: {str(e)}")
            return []
        finally:
            self.disconnect()
    
    def download_response_file(self, filename: str) -> str:
        """
        Download response file from outbound folder
        
        Args:
            filename: Name of file to download
        
        Returns:
            File content as string
        """
        try:
            self.connect()
            
            remote_path = f"{self.outbound_folder}/{filename}"
            
            # Read file content
            with self._sftp_client.file(remote_path, 'r') as remote_file:
                content = remote_file.read()
            
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            logger.info(f"Downloaded response file: {filename} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Failed to download response file {filename}: {str(e)}")
            raise Exception(f"SFTP download failed: {str(e)}")
        finally:
            self.disconnect()
    
    def download_all_responses(self, delete_after_download: bool = False) -> List[dict]:
        """
        Download all response files from outbound folder
        
        Args:
            delete_after_download: Whether to delete files after successful download
        
        Returns:
            List of dicts with 'filename' and 'content'
        """
        responses = []
        
        try:
            self.connect()
            
            # Get list of files
            files = self._sftp_client.listdir(self.outbound_folder)
            
            for filename in files:
                try:
                    remote_path = f"{self.outbound_folder}/{filename}"
                    
                    # Read file
                    with self._sftp_client.file(remote_path, 'r') as remote_file:
                        content = remote_file.read()
                    
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    
                    responses.append({
                        'filename': filename,
                        'content': content,
                        'downloaded_at': datetime.utcnow().isoformat()
                    })
                    
                    # Delete if requested
                    if delete_after_download:
                        self._sftp_client.remove(remote_path)
                        logger.info(f"Deleted file after download: {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to process file {filename}: {str(e)}")
                    continue
            
            logger.info(f"Downloaded {len(responses)} response files")
            return responses
            
        except Exception as e:
            logger.error(f"Failed to download responses: {str(e)}")
            return []
        finally:
            self.disconnect()
    
    def test_connection(self) -> bool:
        """
        Test SFTP connection
        
        Returns:
            True if connection successful
        """
        try:
            self.connect()
            
            # Try to list directories
            self._sftp_client.listdir(self.inbound_folder)
            self._sftp_client.listdir(self.outbound_folder)
            
            logger.info("SFTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SFTP connection test failed: {str(e)}")
            return False
        finally:
            self.disconnect()
