import numpy as np
import matplotlib.pyplot as plt
import ee
from gge.sensors.SatelliteData import SatelliteData
from gge.util import timing_decorator, exception_handler
from typing import Tuple, Union
from datetime import datetime


class CFSV2FOR6H(SatelliteData):
    def __init__(
        self,
        area: Union[Tuple[float, float, float, float], str, None] = None,
        time_range: Union[Tuple[Union[str, datetime], Union[str, datetime]], str, None] = None,
        variables: list = ["Temperature_height_above_ground"],
    ):
        super().__init__(area, time_range)
        self.variables = variables

    @timing_decorator
    def download_data(self):
        collection_id = "NOAA/CFSV2/FOR6H"
        collection = (
            ee.ImageCollection(collection_id).filterBounds(self.area).filterDate(self.time_range[0], self.time_range[1]).select(self.variables)
        )

        count = collection.size().getInfo()
        if count == 0:
            self.logger.info(f"No images found in collection {collection_id} for the given filters.")
            return

        image_list = collection.toList(count)
        for i in range(count):
            image = ee.Image(image_list.get(i))
            try:
                self.images_data.append(self.convert_data(image))
            except Exception as e:
                self.logger.error(f"Error converting image {image.id().getInfo()}: {e}")

    @exception_handler(default_return_value={})
    def convert_data(self, image):
        sample = image.sampleRectangle(region=self.area, defaultValue=0)
        band_data = {}
        for var in self.variables:
            band_data[var] = np.array(sample.get(var).getInfo())
        return {"image_bands": band_data, "time": image.date().format().getInfo(), "metadata": image.getInfo()["properties"]}

    def display_data(self, index, variable):
        data = self.images_data[index]
        if data:
            plt.figure(figsize=(8, 8))
            plt.imshow(data["image_bands"][variable], cmap="viridis")
            plt.colorbar()
            plt.title(f"{variable} at {data['time']}")
            plt.axis("off")
            plt.show()

    def __len__(self):
        return len(self.images_data)

    def __getitem__(self, index):
        return self.images_data[index]

    def __repr__(self):
        return f"<CFSV2FOR6H covering area {self.area} from {self.time_range[0]} to {self.time_range[1]}>"

    def __str__(self):
        return "NOAA CFSV2 FOR6H Data Handler"
