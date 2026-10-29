from PIL import Image, ImageDraw, ImageFont

# Создаём временную иконку (серый робот-силуэт)
img = Image.new('RGBA', (256, 256), (40, 40, 40, 255))
draw = ImageDraw.Draw(img)

# Рисуем простую маску робота
draw.ellipse([60, 40, 196, 180], fill=(200, 200, 210, 255))  # Голова
draw.ellipse([90, 80, 110, 100], fill=(50, 100, 150, 255))   # Левый глаз
draw.ellipse([146, 80, 166, 100], fill=(50, 100, 150, 255))  # Правый глаз
draw.rectangle([80, 140, 176, 150], fill=(120, 120, 130, 255))  # Рот

# Сохраняем
img.save("icon.png")
print("✓ Временная иконка icon.png создана")

img.save("icon.ico", sizes=[(16,16), (32,32), (48,48), (256,256)])
print("✓ Временная иконка icon.ico создана")
print("\n⚠ Замени icon.png на своё изображение робота вручную!")
