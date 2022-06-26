import os
import numpy as np
import matplotlib.pyplot as plt
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


# Class to crop images by horizontal separators
class RowCrop:
    def __init__(self, img, separator_color=None, background_color=[255], ratio=0.9):
        """
        :param img_path: path of the original image
        :param separator_color (optional): if the user know the red color code of the separator (optional)
        :param background_color: image background color in red binary code / by default : 255 (white color)
        """
        self.img = img
        self.separator_color = separator_color
        self.background_color = background_color
        self.ratio = ratio

    def convert_to_red(self):
        """
        convert RBG color image to 0-255 range and red Channel
        :return: array
        """
        if self.img.all() <= 1:
            return (self.img * 255).astype(int)[:, :, 0]
        else:
            return self.img[:, :, 0]

    def get_separator_color(self):
        """
        find the colors of the horizontal lines separators : if the user enter the separator_color, return it
        :return: list of potential color code in red channel
        """
        img = self.convert_to_red()
        width = img.shape[1]

        # creating an empty dictionary : key = color : value = count the number of occurrence of the key color
        colors_dict = dict()
        # updating the dictionary by getting the unique colors in 9 different columns (every 10% of width)
        for i in range(int(width * 0.1), width, int(width * 0.1)):
            lst = np.unique(img[:, i])
            for ele in lst:
                colors_dict[ele] = colors_dict[ele] + 1 if ele in colors_dict.keys() else 1
        for color in self.background_color:
            if color in colors_dict.keys():  # deleting the background color
                colors_dict.pop(color)

        # Selecting the maximum sum of appearance of a color in 9 row positions
        if len(colors_dict) > 0:
            max_values = [sorted(colors_dict.values())[-1]]
            potential_color = [k for k, v in colors_dict.items() if v in max_values]
        else:
            potential_color = []
        return potential_color

    def get_separator_position(self):
        """
        find the position of the horizontal line separator with the previous colors
        :return: dictionary : key = position of the separator line : value = color of the separator line
        """
        img = self.convert_to_red()
        colors = self.get_separator_color()
        height = img.shape[0]
        width = img.shape[1]
        # empty dictionary : key= potential separator position, value = color of the separator
        potential_sep_dict = dict()
        # looping over nine different rows and get the positions where potential colors appear
        # nine position is to be sure not to miss a line in case the separator is discontinued
        for y in range(int(width * 0.1), width, int(width * 0.1)):
            # finding th line with the potential color value
            for color in colors:
                pos = (np.where(img[:, y] == color))[0].tolist()
                for ele in pos:
                    potential_sep_dict[ele] = color
            return potential_sep_dict, height, width

    def get_separator(self):
        img = self.convert_to_red()
        potential_sep_dict, height, width = self.get_separator_position()
        # more testing if the line is a separator : assuming ratio (default 75%) of the line must have the value of the given color
        for pos in list(potential_sep_dict.keys()):
            count_pixel = len(np.where(img[pos, :] == potential_sep_dict[pos])[0])
            if count_pixel < width * self.ratio:
                potential_sep_dict.pop(pos)
        # removing the sequence positions ( if the height of the separator is more than one pixel)
        x_positions = list(potential_sep_dict.keys())
        x_positions.sort()
        x_positions = [v for i, v in enumerate(x_positions) if i == 0 or v != x_positions[i - 1] + 1]
        final_positions_dict = {i: potential_sep_dict[i] for i in x_positions}
        # removing the top and bottom line positions
        if 0 in final_positions_dict:
            final_positions_dict.pop(0)
        if height in final_positions_dict:
            final_positions_dict.pop(height)
        return final_positions_dict

    def crop_image(self):
        """
        crop the original image according to the founded horizontal separators
        :return: list of cropped images
        """
        img = self.img
        x_positions = list(self.get_separator().keys())
        cropped_images = []
        position = 0
        for row in x_positions:
            crop = img[position:row, :]
            cropped_images.append(crop)
            position = row + 1

        final_crop = img[position:, :]
        if final_crop.size > 1:
            cropped_images.append(final_crop)
        return cropped_images  # list of cropped images

    @staticmethod
    def row_data(crops):
        """
        detect text in the crops with pytesseract
        :return: list of text in crops
        """

        data_list = []
        for crop in crops:
            if crop.all() <= 1:
                crop = crop * 255
            crop_image = np.array(crop).astype(np.uint8)
            data_list.append(pytesseract.image_to_string(crop_image))
        return data_list

    def save_row(self, folder):
        """
        save cropped images into a folder
        :return: saved images in an existing or a new folder
        """
        path = os.getcwd() + '\\' + folder + '\\'
        if not os.path.exists(path):  # if the given path doesn't exist, create a new folder
            os.makedirs(path)
        i = 1
        for crop in self.crop_image():
            image_name = 'Crop_' + str(i) + '.png'
            plt.imsave(path + image_name, crop)
            i += 1

# Class to crop images by horizontal and vertical separators
class FullCrop(RowCrop):
    def __int__(self):
        super().__init__(self, image, separator_color=None, background_color=[255], ratio=0.9)

    def full_crop(self):
        crops = self.crop_image()
        full_crop_lst = []
        for crop in crops:
            crop_rot = RowCrop(np.rot90(crop))
            for el in crop_rot.crop_image():
                elem_rot = np.rot90(el, 3)
                full_crop_lst.append(elem_rot)
        return full_crop_lst

    def crop_data(self):
        return self.row_data(self.full_crop())

    def save_crop(self, folder):
        path = os.getcwd() + '/' + folder + '/'
        if not os.path.exists(path):  # if the given path doesn't exist, create a new folder
            os.makedirs(path)
        i = 1
        for crop in self.full_crop():
            image_name = 'Crop_' + str(i) + '.png'
            plt.imsave(path + image_name, crop)
            i += 1
        print(f'Crops was successfully saved in the folder :  {path}')


if __name__ == '__main__':
    image = plt.imread('testimage.png')
    my_img = FullCrop(image, ratio=0.9)
    # print(my_img.get_separator_position())
    # print(f'Number of cropped images is : {len(my_img.crop_image())}')
    # print(my_img.get_separator_position())
    # print(my_img.rotate())
    my_img.save_crop('111111')
    # print(my_img.get_line_positions())
    # for elem in my_img.full_crop():
    #   plt.imshow(elem)
    # plt.show()
    # i = 1
    # for data in my_img.crop_data():
    #    print(f'***Image {i} data is :\n {data}'.strip())
    #   i += 1
