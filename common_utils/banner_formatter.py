import requests
from PIL import Image
import io

def combine_images(home_logo, vs_image, away_logo, output_path, spacing=20):
    """
    Combines three images (home team logo, versus image, and away team logo) into a single banner image.
    
    Parameters:
    - home_logo: URL or file path of the home team's logo
    - vs_image: File path of the 'versus' image to place between logos
    - away_logo: URL or file path of the away team's logo 
    - output_path: File path where the combined banner should be saved
    - spacing: Pixels of horizontal space between images (default: 20)

    Returns:
    - None. Saves the combined image to the specified output path.
    """
    # Open images
    # image1 = Image.open(home_logo)

    response1 = requests.get(home_logo)
    image1 = Image.open(io.BytesIO(response1.content))

    image2 = Image.open(vs_image)

    # image3 = Image.open(away_logo)

    response3 = requests.get(away_logo)
    image3 = Image.open(io.BytesIO(response3.content))

    # Resize images to have the same height
    min_height = min(image1.height, image2.height, image3.height)
    image1 = image1.resize((int(image1.width * min_height / image1.height), min_height))
    image2 = image2.resize((int(image2.width * min_height / image2.height), min_height))
    image3 = image3.resize((int(image3.width * min_height / image3.height), min_height))

    # Create a new blank image with the combined width and the height of the tallest image
    combined_width = image1.width + image2.width + image3.width + (2 * spacing)
    combined_height = min_height
    combined_image = Image.new(
        "RGBA", (combined_width, combined_height), (255, 255, 255, 0)
    )

    # Paste images onto the new image with spacing
    combined_image.paste(image1, (0, 0))
    combined_image.paste(image2, (image1.width + spacing, 0))
    combined_image.paste(image3, (image1.width + image2.width + (2 * spacing), 0))

    # Save the combined image
    combined_image.save(output_path)

