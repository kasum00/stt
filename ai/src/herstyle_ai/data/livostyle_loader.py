from pathlib import Path

import pandas as pd


class LivostyleLoader:

    def __init__(
        self,
        data_dir: str | Path
    ):

        self.data_dir = Path(data_dir)

        self.products_path = (
            self.data_dir
            / "products.parquet"
        )

        self.images_path = (
            self.data_dir
            / "images.parquet"
        )

        self.variants_path = (
            self.data_dir
            / "variants.parquet"
        )

        self.collections_path = (
            self.data_dir
            / "collections.parquet"
        )

    def load_products(self):

        return pd.read_parquet(
            self.products_path
        )

    def load_images(self):

        return pd.read_parquet(
            self.images_path
        )

    def load_variants(self):

        return pd.read_parquet(
            self.variants_path
        )

    def load_collections(self):

        return pd.read_parquet(
            self.collections_path
        )

    def load_all(self):

        return {
            "products": self.load_products(),
            "images": self.load_images(),
            "variants": self.load_variants(),
            "collections": self.load_collections(),
        }

    def load_product_images(self):

        products = self.load_products()
        images = self.load_images()

        primary_images = images[
            images["image_index"] == 0
        ].copy()

        merged = products.merge(
            primary_images[
                [
                    "product_id",
                    "image_url",
                    "width",
                    "height",
                    "image_index",
                ]
            ],
            left_on="id",
            right_on="product_id",
            how="left",
        )

        return merged