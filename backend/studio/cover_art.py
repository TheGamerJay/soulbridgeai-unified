# ====================================
# 📁 FILE: backend/studio/cover_art.py
# ====================================
import os
from .utils import new_id

def generate_art(prompt: str, size="1024x1024"):
    try:
        from config import PATHS, USE_DIFFUSERS, OPENAI_API_KEY
        images_dir = PATHS["images"]
    except ImportError:
        images_dir = "images"
        USE_DIFFUSERS = os.getenv("USE_DIFFUSERS", "0") == "1"
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    os.makedirs(images_dir, exist_ok=True)
    out = os.path.join(images_dir, f"{new_id()}.png")

    if USE_DIFFUSERS:
        # Local Stable Diffusion via diffusers
        try:
            from diffusers import StableDiffusionPipeline
            import torch
            pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)
            pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
            img = pipe(prompt).images[0]
            img.save(out)
            return out
        except ImportError:
            raise RuntimeError("diffusers library not available for local image generation")
    else:
        # OpenAI Images (DALL·E)
        if not OPENAI_API_KEY:
            # Create a placeholder image
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (1024, 1024), color='black')
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("arial.ttf", 60)
                except:
                    font = ImageFont.load_default()
                
                # Wrap text
                words = prompt.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) < 40:
                        current_line += word + " "
                    else:
                        lines.append(current_line.strip())
                        current_line = word + " "
                lines.append(current_line.strip())
                
                y = 400
                for line in lines[:3]:  # Max 3 lines
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (1024 - text_width) // 2
                    draw.text((x, y), line, fill='white', font=font)
                    y += 80
                
                img.save(out)
                return out
            except ImportError:
                # Even simpler fallback
                with open(out, 'wb') as f:
                    f.write(b'')  # Empty file as placeholder
                return out
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            res = client.images.generate(model="dall-e-3", prompt=prompt, size=size, n=1)
            url = res.data[0].url
            
            # Download the image
            import requests
            response = requests.get(url)
            with open(out, 'wb') as f:
                f.write(response.content)
            return out
        except Exception as e:
            raise RuntimeError(f"OpenAI image generation failed: {e}")