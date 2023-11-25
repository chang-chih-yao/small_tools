from PIL import Image
w = 24
h = 24
im = Image.open("shuttle.png")
im = im.resize((w, h), resample=Image.LANCZOS)
im.save("output.png")