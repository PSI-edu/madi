import os.path

import localclient
import logging
import pds4
import xml.sax
import functools

logger = logging.getLogger(__name__)


def load_local_bundle(path: str) -> pds4.FullBundle:
    """
    Loads a bundle located at the given path on the filesystsm
    """
    logger.info(f'Loading bundle: {path}')
    filepaths = localclient.get_file_paths(path)
    label_paths = [x for x in filepaths if x.endswith(".xml")]
    product_types = {x: extract_product_type(x) for x in label_paths}

    collections = [localclient.fetchcollection(path)
                   for path in label_paths if is_collection(product_types[path]) and not is_superseded(path)]
    bundles = [localclient.fetchbundle(path)
               for path in label_paths if is_bundle(product_types[path]) and not is_superseded(path)]
    products = [localclient.fetchproduct(path) for path in label_paths if is_basic(product_types[path]) and not is_superseded(path)]

    superseded_collections = [localclient.fetchcollection(path)
                              for path in label_paths if is_collection(product_types[path]) and is_superseded(path)]
    superseded_bundles = [localclient.fetchbundle(path)
                          for path in label_paths if is_bundle(product_types[path]) and is_superseded(path)]
    superseded_products = [localclient.fetchproduct(path)
                           for path in label_paths if is_basic(product_types[path]) and is_superseded(path)]


    if len(bundles) == 0:
        raise Exception(f"Could not find bundle product in: {path}")
    return pds4.FullBundle(path, bundles, superseded_bundles, collections, superseded_collections, products, superseded_products)


def is_basic(product_type: str) -> bool:
    """
    Determines if the type is a basic (non-collection or bundle) product.
    :param product_type:
    :return:
    """
    return not (is_collection(product_type) or is_bundle(product_type))


def is_collection(product_type: str) -> bool:
    """
    Determines if the product type is a collection product
    :param product_type:
    :return:
    """
    return product_type == "Product_Collection"


def is_bundle(product_type: str) -> bool:
    """
    Determines if the product type is a bundle product
    :param product_type:
    :return:
    """
    return product_type == "Product_Bundle"


def is_superseded(filepath: str) -> bool:
    """
    Determines if the product at the given path has been superseded
    :param filepath:
    :return:
    """
    return "SUPERSEDED" in filepath

def extract_product_type(filename: str) -> str:
    """
    Gets the product type from the specified product by parsing the label.
    """
    h = ProductTypeExtractor()
    try:
        with open(filename, "rb") as f:
            xml.sax.parse(f, h)
            return h.productType
        raise ValueError(f"Could not find product type for: {filename}")
    except StopParsingException:
            return f"{h.productType}"
    except Exception as e:
        raise ValueError(f"Could not parse product: {filename}") from e


class ProductTypeExtractor(xml.sax.ContentHandler):
    def __init__(self):
        super().__init__()
        self.productType = None

    def startElement(self, name, attrs):
        if name.startswith("Product"):
            self.productType = name
            raise StopParsingException

    def endDocument(self):
        raise ValueError()


class StopParsingException(Exception):
    pass