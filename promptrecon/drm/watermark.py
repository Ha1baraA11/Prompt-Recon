# file: promptrecon/drm/watermark.py
import binascii

class PromptWatermarker:
    """
    Implements a theoretical DRM system for AI prompts.
    It embeds a unique identifier into text using zero-width spaces, non-joiners, etc.
    These characters are invisible to humans but persist when the prompt is copied
    and pasted by attackers.
    """
    
    # Map binary to zero-width characters
    # 0 = Zero Width Space (U+200B)
    # 1 = Zero Width Non-Joiner (U+200C)
    BIN_MAP = {
        '0': '\u200B',
        '1': '\u200C'
    }
    
    REV_MAP = {v: k for k, v in BIN_MAP.items()}

    def __init__(self, tenant_id="tenant_01"):
        self.tenant_id = tenant_id
        
    def embed_watermark(self, text: str) -> str:
        """
        Embed the tenant ID as a zero-width sequence somewhere in the text.
        """
        # Convert tenant_id string to binary String
        binary_id = ''.join(format(ord(c), '08b') for c in self.tenant_id)
        
        # Convert binary string to zero-width characters
        zw_string = ''.join(self.BIN_MAP[b] for b in binary_id)
        
        # Insert it after the first word or at the beginning
        parts = text.split(" ", 1)
        if len(parts) == 2:
            return parts[0] + zw_string + " " + parts[1]
        return zw_string + text

    def extract_watermark(self, text: str) -> str:
        """
        Attempt to extract a tenant ID from zero-width characters in the text.
        """
        binary_str = ""
        for char in text:
            if char in self.REV_MAP:
                binary_str += self.REV_MAP[char]
                
        if not binary_str:
            return None
            
        # Reconstruct characters
        chars = []
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))
        return "".join(chars)

# Example:
# wm = PromptWatermarker("my_corp_x1")
# w_text = wm.embed_watermark("You are a helpful assistant")
# print(wm.extract_watermark(w_text)) # outputs my_corp_x1
