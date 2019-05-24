import os
import time
import logging
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
import itertools

logger = logging.getLogger()
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urrlib3").setLevel(logging.WARNING)
temps_debut = time.time()


def get_soup(url):
    return BeautifulSoup(requests.get(url).content, features="lxml")


def get_categories(url):
    soup_index = get_soup(url)
    urls_cat = []

    links_index = soup_index.find_all("div", {"class": "category-block"})
    for cat in links_index:
        urls_cat.append(str(cat.find("a")["href"]))
    return urls_cat


def get_products(url):
    soup_cat = get_soup(url)
    urls_products = []
    products = soup_cat.find_all("a", {"class": "product-link"})
    if not products:
        return urls_products
    for product in products:
        urls_products.append(product["href"])
    return urls_products


def get_specs(url):
    product = {}
    soup_product = get_soup(url)
    product["Nom"] = str(
        soup_product.find("div", {"class": "title-box"})
        .find("h1")
        .text.strip()
    )
    product["Lien"] = url
    product["Prix"] = "".join(
        soup_product.find("span", {"class": "price"}).find(text=True).split()
    )
    product["Description"] = str(
        soup_product.find("div", {"class": "fiche-desc"}).text.strip()
    )
    identity_card = soup_product.find("div", {"class": "block-id-card"})
    try:
        intitules = identity_card.find_all("div", {"class": "intitule"})
        valeurs = identity_card.find_all("div", {"class": "value"})
        for i, v in zip(intitules, valeurs):
            intitule = str(i.text.replace(":", "").rstrip())
            valeur = str(v.text.strip())
            product[intitule] = valeur
    except Exception as e:
        logger.error("identity_card error : %s", e)
    logger.debug("product : %s", product)
    return product


def main():
    args = parse_args()

    url = "https://www.aroma-zone.com/tous-nos-produits.html"
    urls_cat = get_categories(url)

    all_products = []
    for url_cat in urls_cat:
        logger.debug("Catégorie : %s", url_cat)
        page_number = 1
        while True:
            url_cat = f"{url_cat.split('&p=', 1)[0]}&p={page_number}"
            products_list = get_products(url_cat)
            if not products_list:
                break
            all_products.append(products_list)
            page_number = page_number + 1

    all_products = list(itertools.chain.from_iterable(all_products))
    products_dict = {}
    for index, product in enumerate(all_products):
        logger.debug("all_products : %s - %s", index, product)
        product_dict = get_specs(product)
        products_dict[index] = product_dict

    directory = "Exports"
    if not os.path.exists(directory):
        logger.debug("Creating Exports Folder")
        os.makedirs(directory)

    df = pd.DataFrame.from_dict(products_dict, orient="index")
    try:
        filename = f"{directory}/aromazone_data.csv"
        print(f"Writing {filename}")
        df.to_csv(filename, sep=";")
    except Exception as e:
        logger.error("Error exporting products_dict : %s", str(e))

    print("Runtime : %.2f seconds" % (time.time() - temps_debut))


def parse_args():
    parser = argparse.ArgumentParser(description="Scraper aroma-zone.")
    parser.add_argument(
        "--debug",
        help="Display debugging information",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    return args


if __name__ == "__main__":
    main()
