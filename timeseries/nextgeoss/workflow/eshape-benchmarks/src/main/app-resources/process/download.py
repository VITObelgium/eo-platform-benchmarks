import argparse
import logging

from terracatalogueclient import Catalogue, ProductFile

"""

"""

# ---------------------------------------------------------
#                  Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------------------------------------
#                  Argument parser
# ---------------------------------------------------------
parser = argparse.ArgumentParser(description='Download a file using the TerraScope client')
parser.add_argument('-p', required=True, action='store', nargs='+', dest='products', help='Product to download')
parser.add_argument('-o', required=True, action='store', dest='output', help='Output path to store files')
args = parser.parse_args()

if __name__ == '__main__':
    catalogue = Catalogue()
    catalogue.authenticate_non_interactive(username='eshape-benchmark', password='rD2bswtP%v#Bb6wU%3SF')
    basename = args.products[0].split('/')[9]
    for product in args.products:
        catalogue.download_file(ProductFile(href=product, length=None), args.output)
    print(basename)
