import os
import asyncio
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

class ImageGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.images_path = "CustosBot/images"
        os.makedirs(self.images_path, exist_ok=True)
    
    async def generate_with_openai(self, prompt: str, filename: str) -> str:
        """Generate image using OpenAI DALL-E"""
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            # Download the image
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                if image_url:
                    image_response = requests.get(image_url)
                else:
                    raise Exception("No image URL received from OpenAI")
            else:
                raise Exception("No image data received from OpenAI")
            
            if image_response.status_code == 200:
                filepath = os.path.join(self.images_path, filename)
                with open(filepath, 'wb') as f:
                    f.write(image_response.content)
                return filepath
            else:
                raise Exception(f"Failed to download image: {image_response.status_code}")
                
        except Exception as e:
            print(f"OpenAI generation failed: {e}")
            # Fallback to local generation
            return await self.generate_local(prompt, filename)
    
    async def generate_local(self, text: str, filename: str) -> str:
        """Generate image locally using PIL as fallback"""
        try:
            # Create dark themed image
            width, height = 1024, 1024
            background_color = (30, 20, 60)  # Dark purple
            text_color = (255, 255, 255)     # White text
            accent_color = (138, 43, 226)    # Blue violet
            
            image = Image.new('RGB', (width, height), background_color)
            draw = ImageDraw.Draw(image)
            
            # Try to use a nice font, fallback to default
            try:
                font_size = 80
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw accent background
            margin = 50
            draw.rectangle([x-margin, y-margin, x+text_width+margin, y+text_height+margin], 
                         fill=accent_color, outline=None)
            
            # Draw text
            draw.text((x, y), text, fill=text_color, font=font)
            
            # Add decorative elements
            for i in range(5):
                circle_x = 100 + i * 200
                circle_y = 100
                draw.ellipse([circle_x-10, circle_y-10, circle_x+10, circle_y+10], 
                           fill=accent_color)
            
            filepath = os.path.join(self.images_path, filename)
            image.save(filepath)
            return filepath
            
        except Exception as e:
            print(f"Local generation failed: {e}")
            # Return a basic placeholder path
            return os.path.join(self.images_path, filename)
    
    async def generate_main_menu_image(self) -> str:
        """Generate main menu cover image"""
        prompt = """
        Dark themed logo for Telegram bot called 'Custos | Чат-менеджер'. 
        Modern minimalist design with dark purple, blue, black and white colors. 
        Dark background with elegant white text. 
        Futuristic chat management theme with geometric elements.
        No realistic photos, just abstract geometric design.
        """
        return await self.generate_with_openai(prompt, "main_menu.png")
    
    async def generate_commands_image(self) -> str:
        """Generate commands help image"""
        prompt = """
        Dark themed header image with text 'Команды' (Commands in Russian). 
        Dark purple and blue gradient background with white text. 
        Minimalist design with geometric elements and chat symbols.
        Modern tech style, no realistic photos.
        """
        return await self.generate_with_openai(prompt, "commands.png")
    
    async def generate_my_chats_image(self) -> str:
        """Generate my chats image"""
        prompt = """
        Dark themed header image with text 'Мои чаты' (My Chats in Russian). 
        Dark background with purple and blue accents. 
        Chat bubble icons and geometric elements. 
        Modern minimalist style, white text on dark background.
        """
        return await self.generate_with_openai(prompt, "my_chats.png")
    
    async def generate_user_profile_image(self) -> str:
        """Generate user profile description image"""
        prompt = """
        Dark themed image for user profile with text 'Описание чатера' (User Description in Russian).
        Dark purple background with blue accents. 
        User avatar placeholder and profile elements.
        Modern minimalist design with white text.
        """
        return await self.generate_with_openai(prompt, "user_profile.png")
    
    async def generate_bot_avatar(self) -> str:
        """Generate bot avatar"""
        prompt = """
        Bot avatar for 'Custos' chat manager. 
        Circular avatar with dark theme - purple, blue, black colors. 
        Modern robotic or AI assistant appearance. 
        Professional and trustworthy design. 
        No text, just the avatar icon.
        """
        return await self.generate_with_openai(prompt, "bot_avatar.png")

# Create global instance
image_gen = ImageGenerator()