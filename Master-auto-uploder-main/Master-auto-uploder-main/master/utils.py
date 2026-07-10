"""
master/utils.py - Utility functions
Reconstructed from utils.so analysis
"""
import aiohttp
import base64
import random
from Crypto.Cipher import AES
from logger import LOGGER
from config import Config
from master.server import scraper


async def check_server():
    try:
        session = aiohttp.ClientSession()
        response = await session.get("https://www.google.com")
        await session.close()
        if response.status == 200:
            LOGGER.info("Server check: Online")
            return True
        else:
            LOGGER.warning(f"Server check failed with status: {response.status}")
            return False
    except Exception as e:
        LOGGER.error(f"Server check error: {e}")
        return False


async def decrypt_link(link):
    try:
        key = b"testkey123456789"  # 16-byte key
        iv = b"testiv1234567890"   # 16-byte IV
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decoded = base64.b64decode(link)
        decrypted_link = await unpad(cipher.decrypt(decoded), AES.block_size)
        return decrypted_link.decode('utf-8')
    except Exception as e:
        LOGGER.error(f"Decrypt error: {e}")
        return link


async def send_random_photo():
    """Return a random photo URL for bot messages.
    Returns None if no valid photos are configured.
    To add your own photos, upload images to telegra.ph and add URLs below.
    """
    regex_photo = [
        # Add your own telegra.ph image URLs here, e.g.:
        # "https://telegra.ph/file/your-real-image-id.jpg",
    ]
    if not regex_photo:
        return None
    pht = random.choice(regex_photo)
    try:
        response = await scraper.get(pht)
        if response.status_code == 200:
            return pht
        return None
    except:
        return None


async def unpad(padded_data, block_size, style='pkcs7'):
    pdata_len = len(padded_data)
    if pdata_len == 0:
        raise ValueError("Zero-length input cannot be unpadded")
    if pdata_len % block_size:
        raise ValueError("Input data is not padded")
    
    if style == 'pkcs7':
        padding_len = padded_data[-1]
        if padding_len < 1 or padding_len > block_size:
            raise ValueError("Padding is incorrect.")
        if padded_data[-padding_len:] != bytes([padding_len]) * padding_len:
            raise ValueError("PKCS#7 padding is incorrect.")
        return padded_data[:-padding_len]
    else:
        # zero padding
        padding_len = 0
        for i in range(pdata_len - 1, -1, -1):
            if padded_data[i] != 0:
                break
            padding_len += 1
        return padded_data[:pdata_len - padding_len]
