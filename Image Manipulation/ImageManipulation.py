from PIL import Image, ImageDraw, ImageChops, ImageFilter, ImageOps

def round_corners_no_cutoff(image, radius=20, background_color=(0,0,0,0)):
    """
    Creates a new RGBA image bigger than the original,
    applies a rounded rectangle mask so the *outer* corners
    are rounded, but does NOT remove any of the original content.

    :param image: The original image (any mode, but RGBA is ideal).
    :param radius: How big the corner rounding should be.
    :param background_color: The color/alpha behind the corners.
    :return: A new RGBA image with a bigger canvas and rounded corners.
    """
    # 1) Convert and get original size
    image = image.convert("RGBA")
    w, h = image.size

    if radius <= 0:
        # No rounding at all; just return the original
        return image.copy()

    # 2) Compute new size: add 'radius' on each side
    #    so corners won't cut off any original content
    new_w = w + 2 * radius
    new_h = h + 2 * radius

    # 3) Create a new blank image (with background color) at the new size
    new_image = Image.new("RGBA", (new_w, new_h), background_color)

    # 4) Paste the original image in the center
    #    The offset is 'radius' so there's space for the corners
    new_image.paste(image, (radius, radius))

    # 5) Create a mask for the entire new bounding box with rounded corners
    mask = Image.new("L", (new_w, new_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, new_w, new_h], radius=radius, fill=255)

    # 6) Apply this rounded mask to the new image's alpha channel
    rounded = new_image.copy()
    rounded.putalpha(mask)

    return rounded



def add_sharp_border(image, color=(0,0,0,255), width=5):
    """
    Adds a sharp border (no forced rounding) around an object 
    on a transparent background, expanding the canvas so the
    border isn't clipped.

    :param image: RGBA Image (with alpha defining the shape).
    :param color: RGBA tuple for the border color.
    :param width: How many pixels outward to expand.
    :return: A new RGBA image with an expanded canvas and border.
    """
    if width <= 0:
        return image.copy()

    # Convert for safety and get original size
    image = image.convert("RGBA")
    orig_w, orig_h = image.size

    # 1) Expand the canvas to accommodate the border
    new_w, new_h = orig_w + 2*width, orig_h + 2*width
    expanded_img = Image.new("RGBA", (new_w, new_h), (0,0,0,0))
    # Paste original in the middle so there's 'width' padding all around
    expanded_img.paste(image, (width, width))

    # 2) Get the alpha channel from the new expanded canvas
    alpha = expanded_img.getchannel("A")

    # 3) Morphological expansion for a sharp border
    #    (MaxFilter uses a square kernel ~ 2*width+1)
    dilated = alpha.filter(ImageFilter.MaxFilter(size=(2*width + 1)))

    # 4) The "border ring" is the difference between dilated alpha and original alpha
    border_mask = ImageChops.subtract(dilated, alpha)
    # Slight blur to reduce severe stepping
    border_mask = border_mask.filter(ImageFilter.GaussianBlur(0.5))

    # 5) Create a layer for the border color
    border_layer = Image.new("RGBA", expanded_img.size, color)
    border_layer.putalpha(border_mask)

    # 6) Composite the border behind the expanded image
    out = Image.alpha_composite(border_layer, expanded_img)
    return out

    return Image.alpha_composite(border_layer, image)




def add_shadow_no_cutoff(image, shadow_color=(0, 0, 0, 100), offset=(5, 5), sigma=10, extra_padding=0):
    """
    Adds a soft shadow behind an object on a transparent background,
    expanding the canvas so the shadow is not clipped at the edges.

    :param image: The original image (preferably RGBA).
    :param shadow_color: (R, G, B, A) for the shadow.
    :param offset: (dx, dy) shift of the shadow relative to the object.
    :param sigma: Gaussian blur radius for the shadow softness.
    :param extra_padding: Additional pixels of transparent margin around the final result.
    :return: A new RGBA image with shadow fully visible.
    """
    # Ensure RGBA
    image = image.convert("RGBA")
    orig_w, orig_h = image.size

    # 1) Estimate how much we need to expand the canvas
    #    We'll add max(|dx|, sigma) plus extra_padding on each side
    #    to ensure shadow is not cut off.
    dx, dy = offset

    # The blur can extend ~sigma pixels in all directions
    # Also consider offset could be negative or positive
    expand_left   = max(sigma - dx, sigma, 0) + extra_padding
    expand_top    = max(sigma - dy, sigma, 0) + extra_padding
    expand_right  = max(dx, 0) + sigma + extra_padding
    expand_bottom = max(dy, 0) + sigma + extra_padding

    # Compute new canvas size
    new_w = int(orig_w + expand_left + expand_right)
    new_h = int(orig_h + expand_top + expand_bottom)

    # 2) Create a new transparent image
    new_image = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))

    # 3) Paste original image into this new canvas
    #    with offsets for left/top
    paste_x = int(expand_left)
    paste_y = int(expand_top)
    new_image.paste(image, (paste_x, paste_y))

    # 4) Create shadow from alpha channel
    alpha = image.getchannel("A")

    # We'll place the shadow at (paste_x+dx, paste_y+dy)
    shadow_x = paste_x + dx
    shadow_y = paste_y + dy

    # 5) Create a grayscale "shadow" mask on the new canvas
    shadow_mask = Image.new("L", (new_w, new_h), 0)
    shadow_mask.paste(alpha, (shadow_x, shadow_y), alpha)

    # 6) Blur the shadow
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(sigma))

    # 7) Create the shadow layer
    shadow_layer = Image.new("RGBA", (new_w, new_h), shadow_color)
    shadow_layer.putalpha(shadow_mask)

    # 8) Composite shadow behind the new image
    final = Image.alpha_composite(shadow_layer, new_image)
    return final


# User Input
i = int(input("Enter 1: Round       2: Border       3: Shadow\n"))
imgNum = int(input("Enter 0: 000       1: 001       2: 002\n"))

image = Image.open(f"00{imgNum}.png").convert("RGBA")

if i == 1:
    # Apply rounded corners
    rounded_image = round_corners_no_cutoff(image, radius=20)
    rounded_image.save("rounded_image.png")

elif i == 2:
    bordered_img = add_sharp_border(image, color=(0,0,0,255), width=10)
    bordered_img.save("bordered_image2.png")

elif i == 3:
    # Add a shadow
    add_shadow_image = add_shadow_no_cutoff(image, shadow_color=(0, 0, 0, 100), offset=(10, 10), sigma=15)
    add_shadow_image.save("add_shadow_image.png")
