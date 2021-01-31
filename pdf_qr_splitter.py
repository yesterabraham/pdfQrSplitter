try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PIL import Image
    import fitz
    from pyzbar.pyzbar import decode, ZBarSymbol
    import cv2
    import numpy as np
    import imagehash
    from pprint import pprint
    import os
except Exception as e:
    print(e)
    raise("Import ERROR! Some libraries not installed!")

def create_pdf(filename, start_page_number, end_page_namber, pdf_reader):
    print(start_page_number, end_page_namber, filename)
    pdf_writer = PdfFileWriter()
    for page in range(start_page_number, end_page_namber):
        pdf_writer.addPage(pdf_reader.getPage(page))
    with open(filename, 'wb') as file:
        pdf_writer.write(file)


def split_pdf_by_qrcode(filename, page_numbers):
    print("Splitting PDF")
    pdf_reader = PdfFileReader(open(filename, "rb"))
    start_page_number = 0
    for page_number_data in page_numbers:
        page_number = page_number_data[0]
        current_filename = page_number_data[1].decode("utf-8") +".pdf"
        print("Creating pdf from %d page to %d page by %s name" % (start_page_number, page_number, current_filename))
        create_pdf(current_filename, start_page_number, page_number, pdf_reader)
        start_page_number = page_number
    current_filename = page_number_data[1].decode("utf-8")  + ".pdf"
    print("Creating pdf from %d page to %d page by %s name" % (page_number_data[0], pdf_reader.getNumPages(), current_filename))
    create_pdf(current_filename, page_number_data[0], pdf_reader.getNumPages(), pdf_reader)

def get_qr_data(filename):
    # global variables for qr code extraction
    return_data = []
    real_values = []
    found_data = []
    #check_values = [0, 6, 8, 11, 15, 18, 22, 24, 30, 32, 34, 36, 38, 40, 42, 45, 50]

    print("Reading given %s pdf file" % filename)
    doc = fitz.open(filename)
    zoom = 4  # to increase the resolution
    mat = fitz.Matrix(zoom, zoom)
    noOfPages = doc.pageCount
    print("Given pdf has %d pages" % noOfPages)

    print("Starting page by page qr code detection and extraction")
    for pageNo in range(noOfPages):
        print("--------------Page Number %d------------------" % pageNo)
        page = doc.loadPage(pageNo)  # number of page
        pix = page.getPixmap(matrix=mat)
        output = str(pageNo) + '.jpg'  # you could change image format accordingly
        print("Saving image for current page")
        pix.writePNG(output)
        print("Reading saved image for current page")
        img = cv2.imread(output)

        found = False
        print("Detecting QR code...")
        for delta_max_x in range(0, 200, 20):
            if found:
                found = False
                break
            for delta_max_y in range(0, 200, 20):
                if found:
                    break
                for delta in range(0, 50, 1):
                    y = 205 + delta
                    x = 2225
                    h = 115 - delta
                    w = 90
                    max_x = 900 - delta_max_x
                    max_y = 700 + delta_max_y

                    resized_cropped = img[y:y + h, x:x + w]
                    resized_cropped = cv2.resize(resized_cropped, (max_x, max_y))
                    sharpen_filter = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]])
                    resized_cropped = cv2.filter2D(resized_cropped, -1, sharpen_filter)
                    # resized_cropped = cv2.cvtColor(resized_cropped, cv2.COLOR_BGR2GRAY)
                    # _, resized_cropped = cv2.threshold(resized_cropped, 10, 255, cv2.THRESH_OTSU)

                    qr_file = "QR_Code%d.png" % pageNo
                    cv2.imwrite(qr_file, resized_cropped)

                    hash = imagehash.average_hash(Image.open(qr_file))
                    otherhash = imagehash.average_hash(Image.open('QR_Code_example.png'))

                    if (hash - otherhash) < 20:
                        barcodes = decode(resized_cropped, symbols=[ZBarSymbol.QRCODE])
                        if len(barcodes) > 0:
                            print("Qr code detected and extracted!")
                            print(" %d qr code is" % pageNo, barcodes[0].data)
                            real_values.append(pageNo)
                            return_data.append([pageNo, barcodes[0].data])
                            found = True
                            found_data.append([pageNo, y, h, delta_max_x, delta_max_y, delta])
                            break
                    else:
                        if delta == 0:
                            found = True
                            break
        try:
            os.remove(qr_file)
            os.remove(output)
        except:
            pass

    #print("diff = ", set(check_values) - set(real_values))
    pprint(found_data)
    return return_data




if __name__=="__main__":
    filename = "test.pdf"
    qr_code_data = get_qr_data(filename)
    split_pdf_by_qrcode(filename, qr_code_data)